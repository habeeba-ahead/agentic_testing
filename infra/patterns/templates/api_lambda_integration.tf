// infra/patterns/templates/api_lambda_integration.tf
# Generic HTTP API → Lambda integration + route + (optional) stage.
variable "api_id"         { type = string }
variable "function_arn"   { type = string }
variable "route_key"      { type = string }   # e.g., "POST /orders"
variable "auto_stage"     { type = bool   default = true }
variable "stage_name"     { type = string default = "staging" }

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = var.function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "route" {
  api_id    = var.api_id
  route_key = var.route_key
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "api_invoke" {
  statement_id  = "AllowInvokeFromHttpApi-${replace(var.route_key, " ", "_")}"
  action        = "lambda:InvokeFunction"
  function_name = var.function_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:*:*:${var.api_id}/*/*/*"
}

resource "aws_apigatewayv2_stage" "stage" {
  count       = var.auto_stage ? 1 : 0
  api_id      = var.api_id
  name        = var.stage_name
  auto_deploy = true
}
