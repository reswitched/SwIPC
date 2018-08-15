module SwIPC
  module Mergeable
    def can_merge?(other)
      mergeable_properties.each_pair do |prop, mode|
        a = self.instance_variable_get(prop)
        b = other.instance_variable_get(prop)
        case mode
        when :nillable
          if a != nil && b != nil && a != b then
            return false
          end
        when :nillable_mergeable
          if a != nil && b != nil && !a.can_merge?(b) then
            return false
          end
        when :exact
          if a != b then
            return false
          end
        when :nillable_array_mergeable_content
          if a != nil && b != nil then
            if a.length != b.length then
              return false
            end
            a.zip(b).each do |e|
              if e[0] == nil || e[1] == nil then
                return false
              end
              if !e[0].can_merge?(e[1]) then
                return false
              end
            end
          end
        when :nillable_array_nillable_content
          if a != nil && b != nil then
            if a.length != b.length then
              return false
            end
            a.zip(b).each do |e|
              if e[0] != nil && e[1] != nil && e[0] != e[1] then
                return false
              end
            end
          end
        when :array_concat
        when :array_concat_uniq
        when :bool_or
        else
          raise "invalid merge mode '#{mode}'"
        end
      end
      return true
    end

    def merge!(other)
      mergeable_properties.each_pair do |prop, mode|
        a = self.instance_variable_get(prop)
        b = other.instance_variable_get(prop)
        case mode
        when :exact
        when :nillable, :nillable_array_exact_content
          if a == nil then
            instance_variable_set(prop, b)
          else
            if b != nil then
              if a != b then
                raise "can't merge #{prop} with different values: #{a} and #{b}"
              else
                instance_variable_set(prop, b)
              end
            end
          end
        when :nillable_mergeable
          if a == nil then
            instance_variable_set(prop, b)
          else
            if b != nil then
              if !a.can_merge?(b) then
                raise "can't merge #{prop} with different values: #{a} and #{b}"
              else
                instance_variable_set(prop, b)
              end
            end
          end
        when :nillable_array_mergeable_content
          if a == nil then
            if b != nil then
              instance_variable_set(prop, b)
            end
          else
            if b != nil then
              a.zip(b).each do |a, b|
                a.merge!(b)
              end
            end
          end
        when :nillable_array_nillable_content
          if a == nil then
            if b != nil then
              instance_variable_set(prop, b)
            end
          else
            if b != nil then
              instance_variable_set(prop, a.zip(b).map do |a, b|
                                      a || b
                                    end)
            end
          end
        when :array_concat
          instance_variable_set(prop, a.concat(b))
        when :array_concat_uniq
          instance_variable_set(prop, a.concat(b).uniq)
        when :bool_or
          instance_variable_set(prop, a || b)
        else
          raise "invalid merge mode: #{mode}"
        end
      end
      return self
    end
  end
end
