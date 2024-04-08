terraform {
  backend "s3" {
    bucket         = "ra2ce-cluster-deployment" # Update with your S3 bucket name
    key            = "terraform.tfstate"
    region         = "eu-west-1"       # Update with your desired AWS region
  }
}