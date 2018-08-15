module SwIPC
  class Decorator
    def initialize(name, content)
      @name = name
      @content = content
    end
    attr_reader :name
    attr_reader :content
  end

  module Decorators
    class Version
      def initialize(versions, scope=ALL_VERSIONS)
        @versions = versions
        @scope = scope
      end

      def self.parse(content, scope=ALL_VERSIONS)
        single = content.match(/\A([0-9]+\\.[0-9]+\\.[0-9]+)\z/)
        if single then
          return self.new([single[1]], scope)
        end
        terminated_range = content.match(/\A([0-9]+\\.[0-9]+\\.[0-9]+)-([0-9]+\\.[0-9]+\\.[0-9]+)\z/)
        if terminated_range then
          return self.new(scope.slice(scope.index_of(terminated_range[1])..scope.index_of(terminated_range[2])), scope)
        end
        unterminated_range = content.match(/([0-9]+\\.[0-9]+\\.[0-9]+)\\+/)
        if unterminated_range then
          return self.new(scope.drop(scope.index_of(unterminated_range[1])), scope)
        end
        raise "invalid version range: #{content}"
      end

      def to_swipc(version_scope=@scope)
        if @versions.first == version_scope.first && @versions.last == version_scope.last then
          return nil
        end
        if @versions.last == version_scope.last then
          return "@version(#{@versions.first}+)"
        elsif @versions.first == @versions.last then
          return "@version(#{@versions.first})"
        else
          return "@version(#{@versions.first}-#{@versions.last})"
        end
      end
      
      attr_reader :versions

      class << self
        def needed?(versions, version_scope)
          return versions.first != version_scope.first || versions.last != version_scope.last
        end
      end
    end
  end
end
