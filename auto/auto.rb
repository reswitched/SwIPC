require "json"

require_relative "util.rb"
require_relative "data_source.rb"
require_relative "types.rb"
require_relative "buffer.rb"
require_relative "interface.rb"
require_relative "command.rb"
require_relative "context.rb"

class TemplateAST
  def initialize(before, inside, after)
    @before = before.match(/\A(.*?)(?: *const\&)?\z/)[1]
    @inside = inside
    @after = after.match(/\A(.*?)(?: *const\&)?\z/)[1]
  end

  def to_s
    return @before + (@inside ? "<" + (@inside.map do |e| e.to_s end).join(", ") + ">" : "" ) + (@after == "" ? "" : " " + @after)
  end
  
  def self.parse_single(e, force_template_ast=false)
    if e.is_a?(String) then
      e = e.each_char
    end

    before = ""
    inside = nil
    after = ""
    begin
      while e.peek != "<" && e.peek != "," && e.peek != ">" && e.peek != " " do
        before = before + e.next
      end
      if e.peek == "<" || e.peek == " " then
        if e.peek == "<" then
          e.next # skip <
          inside = parse_list(e)
          if e.peek == ">" then
            e.next # skip >
          else
            raise "invalid state"
          end
        end
        while e.peek == " " do e.next end # swallow spaces
        after = ""
        begin
          while e.peek != "<" && e.peek != "," && e.peek != ">" do
            after = after + e.next
          end
        rescue StopIteration
        end
        return self.new(before, inside, after)
      elsif e.peek == "," then
        return force_template_ast ? TemplateAST.new(before, inside, after) : before
      elsif e.peek == ">" then
        return force_template_ast ? TemplateAST.new(before, inside, after) : before
      else
        raise "invalid state"
      end
    rescue StopIteration
    end
    return force_template_ast ? TemplateAST.new(before, inside, after) : before
  end

  def self.parse_list(e, force_template_ast=false)
    if e.is_a?(String) then
      e = e.each_char
    end
    
    arr = []
    begin
      loop do
        while e.peek == " " do e.next end
        s = parse_single(e, force_template_ast)
        arr.push(s)
        if e.peek == "," then
          e.next
        elsif e.peek == ">" then
          return arr
        else
          raise "invalid state: head left at #{e.peek}"
        end
      end
    rescue StopIteration
      return arr
    end
    return arr
  end
  
  attr_reader :before
  attr_reader :inside
  attr_reader :after
end

def add_data_to_command(cmd, key, value)
  case key
  when "inbytes"
    cmd.inbytes = value
  when "outbytes"
    cmd.outbytes = value
  when "buffers"
    cmd.buffers = value.map do |b| SwIPC::Buffer.new(nil, b, nil) end
  when "pid"
    cmd.pid = value
  when "ininterfaces"
    cmd.ininterfaces = value
  when "outinterfaces"
    cmd.outinterfaces = value
  when "inhandles"
    cmd.inhandles = value
  when "outhandles"
    cmd.outhandles = value
  when "name"
    cmd.name = value
  else
    raise "unknown data key: " + key
  end
end

# also infers types on the given version
def add_args_to_command(cmd, data, has_args, has_info, version)
  if has_info then
    cmd.buffers||= []
    cmd.pid||= false
    cmd.ininterfaces||= []
    cmd.outinterfaces||= []
    cmd.inhandles||= []
    cmd.outhandles||= []
    cmd.inargs||= []
    cmd.outargs||= []
  end
  data.each do |arg|
    type = arg[0]
    info = arg[1]
    if info then
      case info.before
      when "Buffer"
        index = SwIPC::parse_int(info.inside[0])
        tx_type = SwIPC::parse_int(info.inside[1])
        size = SwIPC::parse_int(info.inside[2])
        data_type = nil
        
        if type then
          case type.before
          when "Out"
            data_type = type.inside[0].to_s
          when "InArray"
            data_type = type.inside[0].to_s + "[]"
          when "OutArray"
            data_type = type.inside[0].to_s + "[]"
          when "InBuffer"
            data_type = "bytes"
          when "OutBuffer"
            data_type = "bytes"
          else
            data_type = type.to_s
          end
          data_type = cmd.context.get_or_infer_type(data_type)
          data_type.assert_size_on(version, size == 0 ? nil : size)
        end
        cmd.buffers[index] = SwIPC::Buffer.new(data_type, tx_type, size)
      when "InRaw" # <size, alignment, position>
        size = SwIPC::parse_int(info.inside[0])
        alignment = SwIPC::parse_int(info.inside[1])
        position = SwIPC::parse_int(info.inside[2])
        data_type = nil
        if type then
          data_type = cmd.context.get_or_infer_type(type.to_s)
          data_type.assert_size_on(version, size)
          data_type.assert_alignment_on(version, alignment)
        end
        cmd.inargs.push(SwIPC::Command::Arg.new(size, alignment, position, data_type))
        cmd.inargs.sort_by! do |a| a.position end
      when "OutRaw"
        size = SwIPC::parse_int(info.inside[0])
        alignment = SwIPC::parse_int(info.inside[1])
        position = SwIPC::parse_int(info.inside[2])
        if type then
          if type.before != "Out" then
            raise "invalid OutRaw type"
          end
          data_type = cmd.context.get_or_infer_type(type.inside[0].to_s)
          data_type.assert_size_on(version, size)
          data_type.assert_alignment_on(version, alignment)
        end
        cmd.outargs.push(SwIPC::Command::Arg.new(size, alignment, position, data_type))
        cmd.outargs.sort_by! do |a| a.position end
      when "InObject"
        if_type = nil
        if type then
          if type.before != "SharedPointer" then
            raise "invalid InObject type"
          end
          if_type = type.inside[0].to_s
        end
        cmd.ininterfaces[SwIPC::parse_int(info.inside[0])]||= if_type
      when "OutObject"
        of_type = nil
        if type then
          if type.before != "Out" then
            raise "invalid OutObject type: " + type.to_s
          end
          if type.inside[0].before != "SharedPointer" then
            raise "invalid OutObject type: " + type.to_s
          end
          of_type = type.inside[0].inside[0].to_s
        end
        cmd.outinterfaces[SwIPC::parse_int(info.inside[0])]||= of_type
      when "InHandle"
        # type is uninteresting
        cmd.inhandles[SwIPC::parse_int(info.inside[0])] = SwIPC::parse_int(info.inside[1])
      when "OutHandle"
        # type is uninteresting
        cmd.outhandles[SwIPC::parse_int(info.inside[0])] = SwIPC::parse_int(info.inside[1])
      else
        raise "invalid info type: " + info.before
      end
    else
      # TODO: infer?
    end
  end
end

def parseServerData(version, path)
  context = SwIPC::Context.new
  data = JSON.parse(File.read(path))
  data.each_pair do |mod, data|
    source = SwIPC::DataSource.new(version, "server-" + mod)
    data.each_pair do |interface_name, interface_commands|
      if interface_name == "nns::hosbinder::IHOSBinderDriver" then next end # skip IHOSBinderDriver because there are conflicting definitions
      
      i = context.get_or_create_interface(interface_name)
      i.exists_on(version)
      
      interface_commands.each_pair do |id, desc|
        command = SwIPC::Command.new(context, id.to_i, [version], source)
        command.initialize_server_known
        desc.each_pair do |key, value|
          add_data_to_command(command, key, value)
        end
        command.validate
        i.append_command(version, command)
      end
    end
  end
  return context
end

def parseClientData(version, path, desc)
  context = SwIPC::Context.new
  source = SwIPC::DataSource.new(version, "client-" + desc)
  data = JSON.parse(File.read(path))
  data.each_pair do |interface_name, interface_commands|
    if interface_name == "nns::hosbinder::IHOSBinderDriver" then next end # skip IHOSBinderDriver because there are conflicting definitions
    
    i = context.get_or_create_interface(interface_name)
    i.exists_on(version)
    interface_commands.each_pair do |id, desc|
      command = SwIPC::Command.new(context, id.to_i, [version], source)
      desc.each_pair do |key, value|
        if key == "args" || key == "arginfo" then next end
        add_data_to_command(command, key, value)
      end
      args = TemplateAST.parse_list(desc["args"] || "", true)
      arginfo = TemplateAST.parse_list(desc["arginfo"] || "", true)
      if args then
        command.documented = true
      end
      args.fill(nil, args.length...arginfo.length)
      add_args_to_command(command, args.zip(arginfo), desc["args"] != nil, desc["arginfo"] != nil, version)
      command.validate
      i.append_command(version, command)
    end
  end
  return context
end

def applyRegistration(context, data)
  data.each_pair do |service, infos|
    infos.each do |info|
      if info["interface"] == nil then
        #puts "missing interface assignment for #{service}"
        next
      end
      intf = context.get_interface(info["interface"])
      if !intf then
        #puts "missing interface #{info["interface"]}"
        next
      end
      intf.add_registration(SwIPC::ALL_VERSIONS, service)
    end
  end
end

contexts = [
  parseServerData("1.0.0", "auto/newdata/server/data1.json"),
  parseClientData("1.0.0", "auto/newdata/client/data1.json", "0.16.29-from-flog"),
  parseServerData("2.0.0", "auto/newdata/server/data2.json"),
  parseClientData("2.0.0", "auto/newdata/client/data2.json", "1.3.1-from-BoTW120-nnSdk-1_3_1-Release"),
  parseServerData("3.0.0", "auto/newdata/server/data3.json"),
  parseClientData("3.0.0", "auto/newdata/client/data3.json", "3.5.1-from-Odyssey-nnSdk-3_5_1-Release"),
  parseServerData("4.0.0", "auto/newdata/server/data4.json"),
  parseClientData("4.0.0", "auto/newdata/client/data4.json", "4.4.0-from-Hulu"),
]

master_context = contexts.reduce do |memo, obj|
  memo ? memo.merge!(obj) : obj
end

applyRegistration(master_context, JSON.parse(File.read("auto/newdata/registration.json")))

master_context.types.sort_by do |t|
  [t.versions.min, t.versions.max, t.name.to_s]
end.each do |t|
  if t.should_emit? then
    puts t.to_swipc
  end
end

puts ""

puts(master_context.interfaces.sort_by do |i|
       i.name
     end.map do |i|
       i.to_swipc
     end.join("\n"))
