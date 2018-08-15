require "parslet"
require "parslet/convenience"

require_relative "util.rb"
require_relative "data_source.rb"
require_relative "types.rb"
require_relative "buffer.rb"
require_relative "interface.rb"
require_relative "command.rb"
require_relative "context.rb"
require_relative "decorator.rb"

require "pry"

module SwIPC
  class Parser < Parslet::Parser
    rule(:space) {
      (match("\\s") |
       str("//") >> match["^\n"].repeat >> str("\n") >> space?).repeat(1)
    }
    rule(:space?) { space.maybe }
    rule(:integer) {
      (
        (str("0x") >> match["0-9a-fA-F"].repeat(1).as(:int_hex)) |
        match["0-9"].repeat(1).as(:int_dec)
      ) >> space? }

    rule(:name) { match["a-zA-Z_"] >> match["a-zA-Z0-9:_"].repeat }
    rule(:service_name) { match["a-zA-Z_"] >> match["a-zA-Z0-9_:\\-"].repeat }

    rule(:decorator) {
      space? >> str("@") >> name.as(:name) >> (str("(") >> match["^()"].repeat.as(:content) >> str(")")).maybe
    }

    rule(:type) {
      (str("struct") >> space? >> str("{") >> space? >>
       (parameter_definition.as(:member) >> space? >> str(";") >> space?).repeat >> space? >>
       str("}")).as(:struct) |
        name.as(:name) >> template.as(:template).maybe
    }

    rule(:template) {
      str("<") >> template_expression_list >> str(">")
    }
    
    rule(:template_expression_list) {
      template_expression >> (str(",") >> space? >> template_expression).repeat
    }

    rule(:template_expression) {
      type.as(:type) | integer.as(:int)
    }
    
    rule(:type_definition) {
      decorator.as(:decorator).repeat.as(:decorators) >> space? >>
        str("type") >> space? >>
        type.as(:def_type) >> space? >>
        str("=") >> space? >>
        type.as(:src_type) >>
        str(";")
    }

    rule(:service_name_list) {
      service_name.as(:registration) >> space? >> (str(",") >> space? >> service_name.as(:registration) >> space?).repeat >> space?
    }

    rule(:parameter_definition) {
      type.as(:type) >> (space? >> name.as(:name)).maybe >> space?
    }
    
    rule(:parameter_definition_list) {
      parameter_definition.as(:param) >> space? >> (str(",") >> space? >> parameter_definition.as(:param) >> space?).repeat >> space?
    }
    
    rule(:command_definition) {
      decorator.repeat.as(:decorators) >> space? >>
        str("[") >> space? >> integer.as(:command_id) >> space? >> str("]") >> space >>
        name.as(:name) >> str("(") >> parameter_definition_list.maybe.as(:in_values) >> str(")") >> space? >> 
        (str("->") >> space? >> (
           (str("(") >> space? >> parameter_definition_list >> space? >> str(")")) |
           parameter_definition
         )).maybe.as(:out_values) >>
        str(";") >> space?
    }

    rule(:doc_comment) {
      str("#") >> (match["^\n"].repeat.as(:doc) >> str("\n")).maybe >> space?
    }
    
    rule(:interface_definition) {
      decorator.repeat.as(:decorators) >> space? >>
        str("interface") >> space? >>
        name.as(:name) >> space? >>
        (str("is") >> space? >> service_name_list.as(:registrations) >> space?).maybe >>
        str("{") >> space? >>
        (command_definition.as(:command_definition) |
         doc_comment.as(:doc_comment)).repeat.as(:command_definitions) >>
        str("}")
    }
    
    rule(:definition) { (type_definition.as(:type_definition) |
                         interface_definition.as(:interface_definition)) >> space? }
    rule(:definition_list) { definition.repeat(1) }
    root(:definition_list)

    def self.parse_defs(str)
      SwIPC::SwIPCFile.from_ast(self.new.parse_with_debug(str))
    end
  end
  
  class Transform < Parslet::Transform
    rule(:int_hex => simple(:hex)) { hex.to_s.to_i(16) }
    rule(:int_dec => simple(:dec)) { dec.to_s.to_i(10) }
    rule(:int => simple(:int)) { int }

    rule(:name => simple(:name),
         :template => simple(:tem)) { {:name => name, :template => [tem]} }
    rule(:name => simple(:name),
         :template => {
           :type => subtree(:type),
         }) { {:name => name, :template => [{:type => type}]} }
    rule(:param => subtree(:param)) { param }
    
    rule(:decorator => subtree(:decorator)) { Decorator.new(decorator[:name], decorator[:content] || "") }
    rule(:registration => simple(:reg)) { reg }
    rule(:type_definition => subtree(:tdef)) {
      pp tdef
    }
    rule(:command_definition => subtree(:cdef)) {
      def add_value_to_command(c, ast, direction)
        case ast[:type][:name]
        when "pid"
          if ast[:type][:template] then
            line, column = ast[:type][:name].line_and_column
            raise "near #{c.context.filename}:#{line}:#{column}: pid cannot be templated"
          end
          if direction != :in then
            line, column = ast[:type][:name].line_and_column
            raise "#{c.context.filename}:#{line}:#{column}: pid must be in input"
          end
          c.pid = true
        when "handle"
          type = nil
          if ast[:type][:template] && ast[:type][:template].length > 0 then
            if !ast[:type][:template][0][:type] then
              line, column = ast[:type][:name].line_and_column
              raise "near #{c.context.filename}:#{line}:#{column}: invalid handle parameters"
            end
            
            case ast[:type][:template][0][:type][:name]
            when "move"
              {:in => c.inhandles, :out => c.outhandles}[direction].push(2)
            when "copy"
              {:in => c.inhandles, :out => c.outhandles}[direction].push(1)
            when nil
            else
              line, column = ast[:type][:template][0][:type][:name].line_and_column
              raise "#{c.context.filename}:#{line}:#{column}: invalid handle type: '#{ast[:type][:template][0][:type][:name].to_s}'"
            end
          end
          
        when "buffer"
          if !ast[:type][:template] || ast[:type][:template].length != 3 then
            line, column = ast[:type][:name].line_and_column
            raise "#{c.context.filename}:#{line}:#{column}: buffer must have three template parameters"
          end
          data_type, transfer_type, size = ast[:type][:template]
          data_type = c.context.get_type_from_ast(data_type)
          if !transfer_type.is_a? Integer then
            line, column = ast[:type][:name]
            raise "#{c.context.filename}:#{line}:#{column}: invalid buffer transfer type: #{transfer_type}"
          end
          if !size.is_a? Integer then
            if size[:type] && (size[:type][:name] == "unknown" || size[:type][:name] == "variable") then
              size = nil
            else
              line, column = ast[:type][:name]
              raise "#{c.context.filename}:#{line}:#{column}: invalid buffer size: '#{size}'"
            end
          end
          c.buffers.push(Buffer.new(data_type, transfer_type, size))
          
        when "array"
          if !ast[:type][:template] || ast[:type][:template].length != 2 then
            line, column = ast[:type][:name].line_and_column
            raise "#{c.context.filename}:#{line}:#{column}: array must have two template parameters"
          end
          data_type, transfer_type = ast[:type][:template]
          data_type = c.context.get_type_from_ast(data_type)
          if !transfer_type.is_a? Integer then
            line, column = ast[:type][:name]
            raise "#{c.context.filename}:#{line}:#{column}: invalid buffer transfer type: #{transfer_type}"
          end
          c.buffers.push(Buffer.new(data_type, transfer_type, nil, true))
          
        when "object"
          if !ast[:type][:template] || ast[:type][:template].length != 1 then
            line, column = ast[:type][:name].line_and_column
            raise "#{c.context.filename}:#{line}:#{column}: object must specify interface"
          end
          interface = ast[:type][:template][0]
          if !interface[:type] || !interface[:type][:name] then
            line, column = ast[:type][:name].line_and_column
            raise "near #{c.context.filename}:#{line}:#{column}: interface '#{interface}' is invalid"
          end
          if interface[:type][:template] then
            line, column = interface[:type][:name].line_and_column
            raise "near #{c.context.filename}:#{line}:#{column}: interface cannot be templated"
          end
          {:in => c.ininterfaces, :out => c.outinterfaces}[direction].push(interface[:type][:name])
          
        else
          c.append_arg(c.context.get_type_from_ast(ast[:type]), direction, ast[:name])
        end
      end

      c = Command.new(swipc_context, cdef[:command_id], nil)
      c.initialize_known
      #c.decorators = cdef[:decorators]
      
      if !(/Unknown[0-9]+/.match(cdef[:name])) then
        c.name = cdef[:name]
      end
      
      if cdef[:in_values].is_a? Array then
        cdef[:in_values].each do |value|
          add_value_to_command(c, value, :in)
        end
      elsif cdef[:in_values]
        add_value_to_command(c, cdef[:in_values], :in)
      end
      
      if cdef[:out_values] then
        if cdef[:out_values].is_a? Array then
          cdef[:out_values].each do |value|
            add_value_to_command(c, value, :out)
          end
        else
          add_value_to_command(c, cdef[:out_values], :out)
        end
      end
      
      next c
    }
  end
end
