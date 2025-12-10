# Terraform recipes

# Plan Terraform changes
[group('apply')]
plan env="local" +args="":
  terraform plan --var="environment={{env}}" {{args}}

# Apply Terraform changes
[group('apply')]
apply env="local" +args="":
  terraform apply --var="environment={{env}}" {{args}}

# Destroy infrastructure (with confirmation)
[group('apply')]
destroy env="local":
  @echo "⚠️  WARNING: This will destroy infrastructure!"
  terraform destroy --var="environment={{env}}"

# Format Terraform files
[group('lint')]
fmt env="local":
  terraform fmt --recursive

# Validate Terraform configuration
[group('lint')]
validate env="local":
  terraform validate

# Lint Terraform configuration
[group('lint')]
lint env="local":
  tflint --recursive
