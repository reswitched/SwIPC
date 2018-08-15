class Interface
  def initialize(name, registration=nil)
    @name = name
    @registration = registration
    @versions = []
    @commands = Hash.new
  end

  attr_reader :name
  attr_reader :commands
  attr_reader :versions
  
  def exists_on(version)
    @versions.push(version)
    @versions.uniq!
  end

  def append_command(version, command)
    if !@commands[command.id] then
      @commands[command.id] = CommandGroup.new(self)
    end
    entry = @commands[command.id]
    entry.append(version, command)
  end

  def merge!(other)
    # TODO: registration
    if other.versions.length > 1 then
      raise "can't merge with multiple versions: #{other.versions}"
    end
    @versions = @versions.concat(other.versions).uniq
    other.commands.each_pair do |id, cmd|
      append_command(other.versions.first, cmd.versions.first.command)
    end
    return self
  end
  
  def to_swipc
    out = ""
    if SwIPC::Decorators::Version.needed?(@versions, SwIPC::ALL_VERSIONS) then
      out<<= SwIPC::Decorators::Version.new(@versions, SwIPC::ALL_VERSIONS).to_swipc + "\n"
    end
    out<<= "interface #{name} {\n"

    next_id = nil
    @commands.keys.sort.each do |id|
      if id != next_id && next_id != nil then
        out<<= "\n"
      end
      out<<= @commands[id].to_swipc(@versions).lines.map do |l|
        "\t" + l
      end.join + "\n"
      next_id = id + 1
    end
    
    out<<= "}\n"
  end

  # represents a group of command definitions that all share one ID
  class CommandGroup
    def initialize(interface)
      @interface = interface
      @versions = []
    end

    attr_reader :versions
    
    class CommandEntry
      def initialize(command, versions)
        @command = command
        @versions = versions
      end
      attr_accessor :command
      attr_accessor :versions
    end
    
    def append(version, command)
      v = version.split(".").map do |i| i.to_i end
      if @latest_version && ((v <=> @latest_version) < 0) then
        raise "add command entries in version order please"
      end
      if @latest && @latest.command.can_merge?(command) then
        @latest.command.merge!(command)
        if !@latest.versions.include?(version) then
          @latest.versions.push(version)
        end
      else
        if @latest_version && @latest_version == v then
          puts "can't merge two commands from same version #{v} for #{@interface.name}##{command.id}:"
          puts "  " + @latest.command.inspect
          puts "  " + command.inspect
          raise "failure"
        end
        if @latest && @latest.versions.include?(version) then
          @latest.versions.delete version
        end
        e = CommandEntry.new(command, [version])
        @versions.push(e)
        @latest = e
        @latest_version = v
      end
    end

    def to_swipc(version_scope=ALL_VERSIONS)
      @versions.map do |v|
        out = ""
        if SwIPC::Decorators::Version.needed?(v.versions, version_scope) then
          out<<= SwIPC::Decorators::Version.new(v.versions, version_scope).to_swipc + "\n"
        end
        out<<= v.command.to_swipc
        next out
      end.join("\n")
    end
  end
end
