terraform {
  backend "s3" {
    key     = "global.tfstate"
    encrypt = "true"
  }
}
