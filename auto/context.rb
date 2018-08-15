module SwIPC
  class Context
    def initialize(filename="<input>")
      @filename = filename
      @types = {}
      @interfaces = {}
      add_builtin_int_type("char", 1)
      add_builtin_int_type("short", 2)
      add_builtin_int_type("int", 4)
      add_builtin_int_type("long", 8)
      add_builtin_type("float", 4, "f")
      add_builtin_type("bool", 1, "b")
      @types["data"] = DataType.new()
      @types["bytes"] = BytesType.new(true)
      @types["unknown"] = BytesType.new(false)
      # struct
    end

    attr_reader :filename
    
    def get_or_create_interface(name)
      if !@interfaces[name] then
        @interfaces[name] = Interface.new(name)
      end
      return @interfaces[name]
    end

    def get_type(name)
      @types[name]
    end
    
    def get_or_infer_type(name)
      if !@types[name] then
        @types[name] = InferredType.new(name)
      end
      return @types[name]
    end

    def get_type_from_ast(ast)
      if ast[:type] then
        ast = ast[:type]
      end
      if ast[:name] == "unknown" then
        if ast[:template] then
          if ast[:template].length != 1 then
            line, column = ast[:name].line_and_column
            raise "#{filename}:#{line}:#{column}: invalid 'unknown' specialization: '#{ast[:template]}'"
          end
          return AnonymousType.new(ast[:template][0], false)
        else
          return nil
        end
      end
      t = @types[ast[:name].to_s]
      if !t then
        line, column = ast[:name].line_and_column
        raise "#{filename}:#{line}:#{column}: unknown type '#{ast[:name]}'"
      end
      if ast[:template] then
        return t.specialize(ast[:template], self, ast[:name].line_and_column)
      else
        return t
      end
    end

    def define_type(name, existing, versions)
      @types[name]||= AliasedType.new(name)
      versions.each do |v|
        @types[name].alias_on(v, existing)
      end
    end
    
    def types
      @types.values
    end

    def interfaces
      @interfaces.values
    end

    def add_builtin_int_type(name, size)
      {"signed " => "i", "unsigned " => "u", "" => "u"}.each_pair do |prefix, c|
        t = BuiltinType.new(prefix + name, size, c)
        @types[prefix + name] = t
        @types[t.name] = t
      end
    end

    def add_builtin_type(name, size, c)
      t = BuiltinType.new(name, size, c)
      @types[name] = t
      @types[t.name] = t
    end

    def merge!(other)
      other.interfaces.each do |intf|
        if @interfaces[intf.name] then
          @interfaces[intf.name].merge! intf
        else
          @interfaces[intf.name] = intf
        end
      end
      other.types.each do |type|
        if @types[type.name] then
          @types[type.name].merge! type
        else
          @types[type.name] = type
        end
      end
      return self
    end
  end
end
