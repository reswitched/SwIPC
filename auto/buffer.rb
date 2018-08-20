require_relative "mergeable.rb"

module SwIPC
  class Buffer
    include Mergeable
    
    def initialize(data_type, transfer_type, size)
      @data_type = data_type
      @transfer_type = transfer_type
      @size = size
    end

    attr_reader :data_type
    attr_reader :transfer_type
    attr_reader :size

    def mergeable_properties
      {
        :@data_type => :nillable_mergeable,
        :@transfer_type => :exact,
        :@size => :nillable,
      }
    end

    def ==(other)
      (other.is_a? Buffer) &&
        (@data_type == other.data_type) &&
        (@transfer_type == other.transfer_type) &&
        (@size == other.size)
    end
    
    def to_swipc
      type_str = "unknown"
      if @data_type then
        type_str = @data_type.name
      else
        if @size != nil && @size != 0 then
          type_str = "unknown<0x#{@size.to_s(16)}>"
        end
      end
      return "buffer<#{type_str}, 0x#{@transfer_type.to_s(16)}>"
    end

    def to_s
      to_swipc
    end
  end
end
