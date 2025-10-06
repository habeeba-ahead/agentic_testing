// infra/patterns/templates/event_bus.tf
variable "bus_name" { type = string }

resource "aws_cloudwatch_event_bus" "this" {
  name = var.bus_name
  tags = var.tags
}

output "bus_name" { value = aws_cloudwatch_event_bus.this.name }
output "bus_arn"  { value = aws_cloudwatch_event_bus.this.arn  }
