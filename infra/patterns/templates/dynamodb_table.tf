// infra/patterns/templates/dynamodb_table.tf
variable "table_name"          { type = string }
variable "billing_mode"        { type = string  default = "PAY_PER_REQUEST" }
variable "hash_key"            { type = string }
variable "range_key"           { type = string  default = null }
variable "attributes" { # [{ name="pk", type="S" }, ...]
  type = list(object({ name = string, type = string }))
}
variable "ttl_attribute"       { type = string  default = null }
variable "enable_stream"       { type = bool    default = false }
variable "stream_view_type"    { type = string  default = "NEW_AND_OLD_IMAGES" }

resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = var.billing_mode
  hash_key     = var.hash_key
  dynamic "range_key" { for_each = var.range_key == null ? [] : [var.range_key]
    content { /* placeholder; range_key must be set at top level */ }
  }

  dynamic "attribute" {
    for_each = var.attributes
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  dynamic "ttl" {
    for_each = var.ttl_attribute == null ? [] : [var.ttl_attribute]
    content {
      attribute_name = var.ttl_attribute
      enabled        = true
    }
  }

  dynamic "stream_enabled" { for_each = var.enable_stream ? [1] : []
    content {}
  }
  stream_enabled   = var.enable_stream
  stream_view_type = var.enable_stream ? var.stream_view_type : null

  tags = var.tags
}

output "table_name" { value = aws_dynamodb_table.this.name }
output "table_arn"  { value = aws_dynamodb_table.this.arn  }
