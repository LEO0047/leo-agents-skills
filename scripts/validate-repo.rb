#!/usr/bin/env ruby
# frozen_string_literal: true

require "open3"
require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).join("..").realpath
ALLOWED_COMPAT = %w[claude-code codex].freeze
EXPECTED_COMPAT = {
  "claude" => ["claude-code"],
  "codex" => ["codex"],
  "shared" => %w[claude-code codex]
}.freeze

errors = []
skill_names = {}
skill_files = Dir.glob(ROOT.join("skills/*/*/SKILL.md")).sort

skill_files.each do |path|
  relative = Pathname.new(path).relative_path_from(ROOT).to_s
  body = File.read(path)
  match = body.match(/\A---\s*\n(.*?)\n---\s*\n/m)

  unless match
    errors << "#{relative}: missing YAML frontmatter"
    next
  end

  begin
    metadata = YAML.safe_load(match[1], permitted_classes: [], aliases: false)
  rescue Psych::Exception => e
    errors << "#{relative}: invalid YAML frontmatter: #{e.message.lines.first.strip}"
    next
  end

  metadata = {} unless metadata.is_a?(Hash)
  name = metadata["name"].to_s
  directory_name = File.basename(File.dirname(path))
  bucket = relative.split("/")[1]
  compat = Array(metadata["compat"])

  errors << "#{relative}: name must equal directory #{directory_name.inspect}" unless name == directory_name
  errors << "#{relative}: description is required" if metadata["description"].to_s.strip.empty?
  errors << "#{relative}: unsupported compat #{(compat - ALLOWED_COMPAT).inspect}" unless (compat - ALLOWED_COMPAT).empty?
  errors << "#{relative}: compat #{compat.inspect} does not match #{bucket}/" unless compat.sort == EXPECTED_COMPAT.fetch(bucket).sort

  if skill_names.key?(name)
    errors << "#{relative}: duplicate skill name also used by #{skill_names[name]}"
  else
    skill_names[name] = relative
  end
end

Dir.glob(ROOT.join("**/*.{yaml,yml}")).sort.each do |path|
  relative = Pathname.new(path).relative_path_from(ROOT).to_s
  begin
    YAML.safe_load(File.read(path), permitted_classes: [], aliases: false)
  rescue Psych::Exception => e
    errors << "#{relative}: invalid YAML: #{e.message.lines.first.strip}"
  end
end

Dir.glob(ROOT.join("**/*.md")).sort.each do |path|
  relative = Pathname.new(path).relative_path_from(ROOT).to_s
  File.read(path).scan(/\[[^\]]*\]\(([^)]+)\)/).flatten.each do |raw_target|
    target = raw_target.strip.sub(/\A</, "").sub(/>\z/, "").split("#", 2).first
    next if target.empty? || target.match?(%r{\A(?:https?://|mailto:|/)}) || target.include?("$(")

    resolved = Pathname.new(File.dirname(path)).join(target).cleanpath
    errors << "#{relative}: broken relative link #{raw_target.inspect}" unless resolved.exist?
  end
end

readme = File.read(ROOT.join("README.md"))
skill_files.each do |path|
  relative = Pathname.new(path).relative_path_from(ROOT).to_s
  directory = File.dirname(relative)
  name = File.basename(directory)
  expected_link = "[#{name}](#{directory}/)"
  errors << "README.md: missing skill index entry #{expected_link}" unless readme.include?(expected_link)
end

Dir.glob(ROOT.join("skills/**/scripts/*.sh")).sort.each do |path|
  relative = Pathname.new(path).relative_path_from(ROOT).to_s
  errors << "#{relative}: shell script is not executable" unless File.executable?(path)

  _stdout, stderr, status = Open3.capture3("bash", "-n", path)
  errors << "#{relative}: bash syntax failed: #{stderr.strip}" unless status.success?
end

if errors.empty?
  puts "PASS: #{skill_files.length} skills; frontmatter, compat, names, YAML, links, README index, and shell scripts validated."
  exit 0
end

warn errors.join("\n")
warn "FAIL: #{errors.length} validation error(s)."
exit 1
