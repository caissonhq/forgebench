class Forgebench < Formula
  include Language::Python::Virtualenv

  desc "Adversarial pre-merge QA for coding-agent output"
  homepage "https://forgebench.dev"
  url "https://files.pythonhosted.org/packages/source/f/forgebench/forgebench-VERSION_PLACEHOLDER.tar.gz"
  sha256 "SHA256_PLACEHOLDER"
  license "Apache-2.0"

  depends_on "python@3.12"
  depends_on "git"
  depends_on "gh" => :recommended

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/forgebench", "--version"
    system "#{bin}/forgebench", "doctor"
  end
end