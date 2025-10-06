// infra/patterns/templates/api_http.tf
variable "api_name"       { type = string }                   # e.g., "${var.project}-${var.env}-api"
variable "enable_cors"    { type = bool   default = true }
variable "cors_headers"   { type = list(string) default = ["*"] }
variable "cors_methods"   { type = list(string) default = ["*"] }
variable "cors_origins"   { type = list(string) default = ["*"] }

resource "aws_apigatewayv2_api" "http_api" {
  name          = var.api_name
  protocol_type = "HTTP"

  dynamic "cors_configuration" {
    for_each = var.enable_cors ? [1] : []
    content {
      allow_headers = var.cors_headers
      allow_methods = var.cors_methods
      allow_origins = var.cors_origins
    }
  }

  tags = var.tags
}

# No routes/integrations/stages here (intentionally generic)
output "api_id"       { value = aws_apigatewayv2_api.http_api.id }
output "api_endpoint" { value = aws_apigatewayv2_api.http_api.api_endpoint }
