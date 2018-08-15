require_relative "decorator.rb"

module SwIPC
  class Type
    def should_emit?
      true
    end
    
    def to_swipc
      ""
    end

    def can_merge?(other)
      other.versions.each do |v|
        if other.size_on(v) != self.size_on(v) then
          if other.size_on(v) != nil && self.size_on(v) != nil then
            return false
          end
        end
        if other.alignment_on(v) != self.alignment_on(v) then
          if other.alignment_on(v) != nil && self.alignment_on(v) != nil then
            return false
          end
        end
      end
      return true
    end
    
    def merge!(other)
      other.versions.each do |v|
        assert_size_on(v, other.size_on(v))
        assert_alignment_on(v, other.alignment_on(v))
      end
      return self
    end
  end

  class BuiltinType < Type
    def initialize(name, size, prefix)
      @name = name
      @size = size
      @prefix = prefix
    end

    def name
      @prefix + (@size * 8).to_s
    end
    
    attr_reader :size

    def is_builtin?
      true
    end

    def versions
      ALL_VERSIONS
    end
    
    def size_on(version)
      @size
    end

    def size_on_all(versions)
      @size
    end

    def alignment_on(version)
      @size
    end

    def alignment_on_all(versions)
      @size
    end
    
    def assert_size_on(version, size)
      if size && size != @size then
        raise "builtin type #{name} of size #{@size} is not #{size}"
      end
    end

    def assert_alignment_on(version, alignment)
      if alignment && alignment != @size then
        raise "builtin type #{name} of alignment #{@size.inspect} is not aligned to #{alignment.inspect}"
      end
    end

    def should_emit?
      false
    end
  end

  class DataType < Type
    def initialize()
    end

    def name
      "data"
    end

    def is_builtin?
      true
    end

    def versions
      ALL_VERSIONS
    end
    
    def size_on(version)
      nil
    end

    def size_on_all(versions)
      nil
    end

    def alignment_on(version)
      nil
    end

    def alignment_on_all(versions)
      nil
    end
    
    def assert_size_on(version, size)
      raise "can't assert sizeof(data)" if size != nil
    end

    def assert_alignment_on(version, alignment)
      raise "can't assert alignmentof(data)" if alignment != nil
    end

    def should_emit?
      false
    end
  end

  class InferredType < Type
    def initialize(name)
      @name = name
      @sizes = Hash.new
      @alignments = Hash.new
    end

    attr_reader :name
    attr_reader :sizes
    attr_reader :alignments

    def versions
      @sizes.keys | @alignments.keys
    end
    
    def size_on(version)
      @sizes[version]
    end

    def size_on_all(versions)
      versions.map do |v|
        @sizes[v]
      end.reduce do |memo, obj|
        if memo != obj then
          raise "size of #{@name} differs between specified versions"
        end
        memo
      end
    end
    
    def alignment_on(version)
      @alignments[version]
    end

    def alignment_on_all(versions)
      versions.map do |v|
        @alignments[v]
      end.reduce do |memo, obj|
        if memo != obj then
          raise "alignment of #{@name} differs between specified versions"
        end
        memo
      end
    end
    
    def assert_size_on(version, size)
      if @sizes[version] && size && @sizes[version] != size then
        raise "type '#{@name}' on '#{version}' is already #{@sizes[version]} bytes long, not #{size} bytes"
      end
      @sizes[version] = size
      return self
    end

    def assert_alignment_on(version, alignment)
      if @alignments[version] && alignment && @alignments[version] != alignment then
        raise "type '#{@name}' on '#{version}' is already aligned to #{@alignments[version]} bytes, not #{alignment} bytes"
      end
      @alignments[version] = alignment
      return self
    end

    VERSION_SCOPE = ALL_VERSIONS.drop(1) # TODO: no type information on 1.0.0
    
    def to_swipc
      @sizes.keys.group_by do |v|
        {:size => @sizes[v], :alignment => @alignments[v]}
      end.each_pair.map do |size, versions|
        out = ""
        if SwIPC::Decorators::Version.needed?(versions, VERSION_SCOPE) then
          out<<= SwIPC::Decorators::Version.new(versions, VERSION_SCOPE).to_swipc + "\n"
        end
        szstr = ""
        if size[:size] == size[:alignment] then
          case size[:size]
          when 1
            szstr = "u8"
          when 2
            szstr = "u16"
          when 4
            szstr = "u32"
          when 8
            szstr = "u64"
          when nil
            szstr = "unknown"
          else
            szstr = "bytes<0x#{size[:size].to_s(16)}>"
          end
        else
          if size[:size] == nil then
            szstr = "unknown"
          else
            alignstr = size[:alignment] ? "0x#{size[:alignment].to_s(16)}" : "unknown"
            szstr = "bytes<0x#{size[:size].to_s(16)}, #{alignstr}>"
          end
        end
        out<<= "type #{name} = #{szstr};"
      end.join("\n")
    end  
  end

  class AliasedType < Type
    def initialize(name)
      @name = name
      @aliases = {}
    end

    def alias_on(version, type)
      if @aliases[version] then
        raise "type #{name} on #{version} is already aliased to #{aliases[version]}, can't re-alias to #{type}"
      end
      @aliases[version] = type
    end

    def is_builtin?
      false
    end

    def versions
    end
  end

  class AnonymousType < Type
    def initialize(size, alignment=size, is_known=false)
      @size = size
      @alignment = alignment
      @is_known = false
    end
  end

  class BytesType < Type
    def initialize(is_known)
      @is_known = is_known
    end

    def name
      @is_known ? "bytes" : "unknown"
    end

    def is_builtin?
      true
    end

    def versions
      ALL_VERSIONS
    end

    def size_on(version)
      nil
    end

    def sizes
      {:all => nil}
    end

    def alignment_on(version)
      nil
    end
    
    def assert_size_on(version, size)
      if size != nil then
        raise "attempt to assert #{name} size"
      end
    end

    def assert_alignment_on(version, alignment)
      if alignment != nil then
        raise "attempt to assert #{name} alignment"
      end
    end

    def should_emit?
      false
    end

    def specialize(ast, context, line_and_column)
      if ast.length != 1 && ast.length != 2 then
        raise "#{context.filename}:#{line_and_column[0]}:#{line_and_column[1]}: #{name} takes <size[, alignment]>"
      end
      AnonymousType.new(ast[0], ast[1], @is_known)
    end
  end
end
