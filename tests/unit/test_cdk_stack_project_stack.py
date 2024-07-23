import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_stack_project.cdk_stack_project_stack import CdkStackProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_stack_project/cdk_stack_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkStackProjectStack(app, "cdk-stack-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
