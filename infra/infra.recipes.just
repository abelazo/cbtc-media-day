# Terraform recipes

# Workspaces
workspace env:
  terraform workspace select {{ lowercase(env) }}

# Plan Terraform changes
[group('apply')]
plan env +args="":
  terraform plan --var="environment={{ env }}" {{ args }}

# Apply Terraform changes
[group('apply')]
apply env +args="":
  terraform apply --var="environment={{ env }}" {{ args }}

# Apply all changes
[group('apply')]
init-apply env +args="": (init env) (workspace env) (apply env args)

# Destroy infrastructure (with confirmation)
[group('apply')]
destroy env:
  @echo "⚠️  WARNING: This will destroy infrastructure!"
  terraform destroy --var="environment={{ env }}"

# Format Terraform files
[group('lint')]
fmt:
  terraform fmt --recursive

# Validate Terraform configuration
[group('lint')]
validate:
  terraform validate

# Lint Terraform configuration
[group('lint')]
lint:
  tflint --recursive

# Check
[group('lint')]
check: fmt validate lint
