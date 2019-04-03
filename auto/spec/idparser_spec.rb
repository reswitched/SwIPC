require "parslet/rig/rspec"
require_relative "../idparser"

RSpec.describe SwIPC::Transform do
  let(:parser) { SwIPC::Parser.new }
  let(:transformer) { SwIPC::Transform.new }

  def context
    @context||= SwIPC::Context.new
  end
  
  def transform(ast)
    transformer.apply(ast, :swipc_context => context)
  end

  def parse_and_transform(text)
    transform(parser.parse(text))
  end

  def parse_and_transform_command(text)
    transform({:command_definition => parser.command_definition.parse(text)})
  end
  
  context "command definitions" do
    context "default command definition" do
      it "should have pid flag set to false" do
        expect(
          parse_and_transform_command("[1] Command();")
        ).to have_attributes(:pid => false)
      end
    end
    context "pid values" do
      it "should error if a pid value is templated" do
        expect {
          parse_and_transform_command("[1] Command(pid<foo>);")
        }.to raise_error.with_message(/pid cannot be templated/)
      end
      it "should error if pid is in output" do
        expect {
          parse_and_transform_command("[1] Command() -> pid;")
        }.to raise_error.with_message(/pid must be in input/)
      end
      it "should set has pid flag on command" do
        expect(
          parse_and_transform_command("[1] Command(pid);")
        ).to have_attributes(:pid => true)
      end
    end
    context "handle values" do
      it "should error on non-move/copy handle types" do
        expect {
          parse_and_transform_command("[1] Command(handle<bar>);")
        }.to raise_error.with_message(/invalid handle type: 'bar'/)
      end
      it "should add an input handle<move> to inhandles with type 2" do
        expect(
          parse_and_transform_command("[1] Command(handle<move>);")
        ).to have_attributes(:inhandles => [2])
      end
      it "should add an output handle<copy> to outhandles with type 1" do
        expect(
          parse_and_transform_command("[1] Command() -> handle<copy>;")
        ).to have_attributes(:outhandles => [1])
      end
    end
    context "buffer values" do
      it "should convert 'buffer<unknown, 0x6, unknown>' to a buffer with transfer_type 6" do
        expect(
          parse_and_transform_command("[1] Command(buffer<unknown, 0x6, unknown>);")
        ).to have_attributes(:buffers => [have_attributes(
                                            :data_type => nil,
                                            :transfer_type => 0x6,
                                            :size => nil,
                                            :is_array => be_falsey)])
      end
      it "should raise error when buffer doesn't have any template parameters" do
        expect {
          parse_and_transform_command("[1] Command(buffer);")
        }.to raise_error.with_message(/buffer must have three template parameters/)
      end
      it "should raise error when buffer has wrong number of template parameters" do
        expect {
          parse_and_transform_command("[1] Command(buffer<1, 2, 3, 4>);")
        }.to raise_error.with_message(/buffer must have three template parameters/)
      end
      it "should raise error when data type is unrecognized" do
        expect {
          parse_and_transform_command("[1] Command(buffer<a, b, c>);")
        }.to raise_error.with_message(/unknown type 'a'/)
      end
      it "should raise error when transfer type is not an integer" do
        expect {
          parse_and_transform_command("[1] Command(buffer<u32, b, c>);")
        }.to raise_error.with_message(/invalid buffer transfer type/)
      end
      it "should raise error when size is invalid" do
        expect {
          parse_and_transform_command("[1] Command(buffer<u32, 6, c>);")
        }.to raise_error.with_message(/invalid buffer size/)
      end
      it "should represent data types and size" do
        expect(
          parse_and_transform_command("[1] Command(buffer<u32, 0x6, 7>);")
        ).to have_attributes(:buffers => [have_attributes(
                                            :data_type => have_attributes(:name => "u32"),
                                            :transfer_type => 0x6,
                                            :size => 7)])
      end
    end
    context "array values" do
      it "should create Buffer objects marked as arrays" do
        expect(
          parse_and_transform_command("[1] Command(array<u32, 0x6>);")
        ).to have_attributes(:buffers => [have_attributes(:transfer_type => 0x6,
                                                          :is_array => true)])
      end
    end
    context "object values" do
      it "should raise error when there is no template parameter" do
        expect {
          parse_and_transform_command("[1] Command(object);")
        }.to raise_error.with_message(/object must specify interface/)
      end
      it "should raise error when interface is templated" do
        expect {
          parse_and_transform_command("[1] Command(object<test::Interface<is_templated>>);")
        }.to raise_error.with_message(/interface cannot be templated/)
      end
      it "should add object to outinterfaces" do
        expect(
          parse_and_transform_command("[1] Command() -> (object<test::Interface>);")
        ).to have_attributes(:outinterfaces => ["test::Interface"])
      end
    end
  end
  
  context "types" do
    it "should convert bytes<0x10, 0x4> to AnonymousType{:size => 16, alignment => 4}" do
      expect(
        context.get_type_from_ast(
          transform(parser.type.parse("bytes<0x10, 0x4>")))
      ).to be_a SwIPC::AnonymousType and have_attributes(:size => 16, :alignment => 4, :is_known => true)
    end
    it "should convert bytes<8> to an anonymous type with size and alignment 8" do
      expect(
        context.get_type_from_ast(
          transform(parser.type.parse("bytes<8>")))
      ).to be_a SwIPC::AnonymousType and have_attributes(:size => 8, :alignment => 8, :is_known => true)
    end
  end
end
