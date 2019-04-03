module SwIPC
  class DataSource
    def initialize(version, desc)
      @version = version
      @desc = desc
    end
    
    def to_s
      "#{@desc}@#{@version}"
    end
  end
end
