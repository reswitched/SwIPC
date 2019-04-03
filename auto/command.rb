require_relative "util.rb"
require_relative "mergeable.rb"

module SwIPC
  class Command
    include Mergeable
    
    def initialize(context, id, versions, source=nil)
      @context = context
      @id = id
      if versions != nil && !versions.is_a?(Array) then
        raise "not an array"
      end
      @sources = source ? [source] : []
      @versions = versions
      initialize_unknown
    end

    def initialize_unknown
      @name = nil
      @buffers = nil
      @pid = nil
      @inbytes = nil
      @outbytes = nil
      @ininterfaces = nil
      @outinterfaces = nil
      @inhandles = nil
      @outhandles = nil
      @documented = false
    end

    def initialize_known
      @name = nil
      @buffers = []
      @pid = false
      @inbytes = 0
      @outbytes = 0
      @ininterfaces = []
      @outinterfaces = []
      @inhandles = []
      @outhandles = []
      @documented = true
    end

    def initialize_server_known
      @buffers = []
      @pid = false
      @inbytes = 0
      @outbytes = 0
      @ininterfaces = []
      @outinterfaces = []
      @inhandles = []
      @outhandles = []
      @documented = false
    end
    
    attr_reader :context
    attr_reader :id
    attr_reader :sources
    attr_accessor :versions
    
    attr_accessor :name
    attr_accessor :buffers
    attr_accessor :pid
    attr_accessor :inbytes
    attr_accessor :outbytes
    attr_accessor :ininterfaces
    attr_accessor :outinterfaces
    attr_accessor :inhandles
    attr_accessor :outhandles
    attr_accessor :inargs
    attr_accessor :outargs
    attr_accessor :documented
    
    def inspect
      {
        :id => @id,
        :name => @name,
        :buffers => @buffers,
        :inargs => @inargs,
        :outargs => @outargs,
        :pid => @pid,
        :inbytes => @inbytes,
        :outbytes => @outbytes,
        :ininterfaces => @ininterfaces,
        :outinterfaces => @outinterfaces,
        :sources => @sources,
        :versions => @versions,
      }.inspect
    end
    
    def append_arg(type, direction, versions, name=nil)
      arr = {:in => @inargs, :out => @outargs}[direction]
      bytes = {:in => @inbytes, :out => @outbytes}[direction]

      align = type.alignment_on_all(versions)
      size = type.size_on_all(versions)
      
      pos = bytes
      pos = pos + (align)
      pos = pos - (pos % align)
      @arr.push(Arg.new(size, align, pos, type))
      
      case direction
      when :in
        @inbytes = pos + size
      when :out
        @outbytes = pos + size
      else
        raise "invalid direction: #{direction}"
      end
    end

    def mergeable_properties
      {
        :@id => :exact,
        :@name => :nillable,
        :@buffers => :nillable_array_mergeable_content,
        :@inargs => :nillable_array_mergeable_content,
        :@outargs => :nillable_array_mergeable_content,
        :@pid => :nillable,
        :@inbytes => :nillable,
        :@outbytes => :nillable,
        :@ininterfaces => :nillable_array_nillable_content,
        :@outinterfaces => :nillable_array_nillable_content,
        :@inhandles => :nillable,
        :@outhandles => :nillable,
        :@sources => :array_concat,
        :@versions => :array_concat_uniq,
        :@documented => :bool_or,
      }
    end
    
    def validate
      if @inargs then
        pos = 0
        @inargs.each do |a|
          old_pos = pos
          pos = pos + (a.alignment - 1)
          pos = pos - (pos % a.alignment)
          if a.position != pos then
            raise "expected #{a.inspect} to be at #{pos}"
          end
          pos = pos + a.size
        end
        if pos != @inbytes then
          raise "total inbytes (#{inbytes}) did not match calculated #{pos}"
        end
      end
      if @outargs then
        pos = 0
        @outargs.each do |a|
          pos = pos + (a.alignment - 1)
          pos = pos - (pos % a.alignment)
          if a.position != pos then
            raise "expected #{a.inspect} to be at #{pos}"
          end
          pos = pos + a.size
        end
        if pos != @outbytes then
          raise "total outbytes (#{outbytes}) did not match calculated #{pos}"
        end
      end
    end

    def name_or_placeholder
      @name || "Unknown#{id}"
    end
    
    def to_swipc
      input = []
      output = []
      if @inargs != nil then
        @inargs.each do |a|
          input.push(a.to_swipc)
        end
      else
        if @inbytes == nil then
          input.push("unknown")
        elsif @inbytes > 0 then
          input.push("unknown<0x#{@inbytes.to_s(16)}>")
        end
      end
      if @outargs != nil then
        @outargs.each do |a|
          output.push(a.to_swipc)
        end
      else
        if @outbytes == nil then
          output.push("unknown")
        elsif @outbytes > 0 then
          output.push("unknown<0x#{@outbytes.to_s(16)}>")
        end
      end
      if @pid then
        input.push("pid")
      end
      if @inhandles then
        inhandles.each do |ih|
          case ih
          when 1
            input.push("handle<copy>")
          when 2
            input.push("handle<move>")
          else
            raise "invalid input handle: " + ih.to_s
          end
        end
      end
      if @outhandles then
        outhandles.each do |oh|
          case oh
          when 1
            output.push("handle<copy>")
          when 2
            output.push("handle<move>")
          else
            raise "invalid output handle: " + oh.to_s
          end
        end
      end
      if @buffers then
        @buffers.each do |b|
          if (b.transfer_type & 1) > 0 then
            input.push(b.to_swipc)
          else
            output.push(b.to_swipc)
          end
        end
      end
      if @ininterfaces then
        @ininterfaces.each do |i|
          input.push("object<#{i || "unknown"}>")
        end
      end
      if @outinterfaces then
        @outinterfaces.each do |i|
          output.push("object<#{i || "unknown"}>")
        end
      end

      str = ""
      
      if !@documented then
        str+= "@undocumented\n"
      end
      
      # build string
      str+= "[#{id}] #{name_or_placeholder}(" +
            input.join(", ") +
            ")"
      
      if output.length > 1 then
        str = str + " -> (" + output.join(", ") + ")"
      elsif output.length == 1 then
        str = str + " -> " + output[0]
      end
      str = str + ";"
    end

    class Arg
      include Mergeable
      
      def initialize(size, alignment, position, data_type)
        @size = size
        @alignment = alignment
        @position = position
        @data_type = data_type
      end
      
      attr_reader :size
      attr_reader :alignment
      attr_reader :position
      attr_reader :data_type

      def mergeable_properties
        {:@size => :exact,
         :@alignment => :exact,
         :@position => :exact,
         :@data_type => :nillable_mergeable}
      end
      
      def to_swipc
        if @data_type then
          return @data_type.name
        else
          if @size == @alignment then
            case @size
            when 1
              return "u8"
            when 2
              return "u16"
            when 4
              return "u32"
            when 8
              return "u64"
            else
              return "bytes<0x#{@size.to_s(16)}>"
            end
          else
            return "bytes<0x#{@size.to_s(16)}, #{@alignment.to_s(16)}>"
          end
        end
      end
    end    
  end
end
