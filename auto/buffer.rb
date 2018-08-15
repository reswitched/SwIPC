require_relative "mergeable.rb"

module SwIPC
  class Buffer
    include Mergeable
    
    def initialize(data_type, transfer_type, size, is_array=nil)
      @data_type = data_type
      @transfer_type = transfer_type
      @size = size
      @is_array = is_array
    end

    attr_reader :data_type
    attr_reader :transfer_type
    attr_reader :size
    attr_reader :is_array

    def mergeable_properties
      {
        :@data_type => :nillable_mergeable,
        :@transfer_type => :exact,
        :@size => :nillable,
        :@is_array => :nillable
      }
    end

    def ==(other)
      (other.is_a? Buffer) &&
        (@data_type == other.data_type) &&
        (@transfer_type == other.transfer_type) &&
        (@size == other.size) &&
        (@is_array == other.is_array)
    end
    
    def to_swipc
      sz_str = "unknown"
      if @size != nil then
        if @size == 0 then
          sz_str = "variable"
        else
          sz_str = "0x" + @size.to_s(16)
        end
      end
      if @is_array then
        if @size != nil && @size != 0 then
          raise "invalid size for array: " + @size.to_s
        end
        return "array<#{@data_type.name || "unknown"}, 0x#{@transfer_type.to_s(16)}>"
      elsif @data_type && @data_type.name == "data" then
        return "buffer<data, 0x#{@transfer_type.to_s(16)}>"
      else
        return "buffer<#{@data_type ? @data_type.name : "unknown"}, 0x#{@transfer_type.to_s(16)}, #{sz_str}>"
      end
    end

    def to_s
      to_swipc
    end
  end
end
