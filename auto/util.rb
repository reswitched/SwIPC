module SwIPC
  ALL_VERSIONS = ["1.0.0", "2.0.0", "3.0.0", "4.0.0"]

  class << self
    def parse_int(str)
      str = str.strip
      if str.match(/0x[A-Fa-f0-9]+/) then
        return str.to_i(16)
      elsif str.match(/[0-9]+/) then
        return str.to_i(10)
      else
        raise "invalid int: " + str
      end
    end
    
    def merge_prop!(a, b, prop)
      aval = a.instance_variable_get(prop)
      bval = b.instance_variable_get(prop)
      if aval == nil then
        a.instance_variable_set(prop, bval)
      else
        if bval != nil then
          if aval != bval then
            raise "can't merge #{prop} with different values: #{aval} and #{bval}"
          else
            a.instance_variable_set(prop, bval)
          end
        end
      end
    end
  end
end
