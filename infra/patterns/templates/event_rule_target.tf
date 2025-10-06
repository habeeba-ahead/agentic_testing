// infra/patterns/templates/event_rule_target.tf
# Generic EventBridge rule → Lambda target
variable "bus_name"     { type = string }
variable "detail_type"  { type = string }
variable "source"       { type = string }
variable "function_arn" { type = string }
variable "rule_name"    { type = string }

resource "aws_cloudwatch_event_rule" "this" {
  name           = var.rule_name
  event_bus_name = var.bus_name
  event_pattern  = jsonencode({ "source":[var.source], "detail-type":[var.detail_type] })
  tags           = var.tags
}

resource "aws_cloudwatch_event_target" "t" {
  rule           = aws_cloudwatch_event_rule.this.name
  event_bus_name = var.bus_name
  arn            = var.function_arn
}

resource "aws_lambda_permission" "events_invoke" {
  statement_id  = "AllowInvokeFromEventBridge-${var.rule_name}"
  action        = "lambda:InvokeFunction"
  function_name = var.function_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
