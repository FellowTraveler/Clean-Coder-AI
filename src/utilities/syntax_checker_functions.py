import ast
import yaml
import sass
from lxml import etree
import re
from src.utilities.print_formatters import print_formatted


def check_syntax(file_content, filename):
    parts = filename.split(".")
    extension = parts[-1] if len(parts) > 1 else ''
    if extension == "py":
        return parse_python(file_content)
    elif extension in ["html", "htm"]:
        return parse_html(file_content)
    elif extension == "js":
        return parse_javascript(file_content)
    elif extension in ["css", "scss"]:
        return parse_scss(file_content)
    elif extension == "vue":
        return parse_vue_basic(file_content)
    elif extension == "tsx":
        return parse_tsx(file_content)
    elif extension in ["yml", "yaml"]:
        return parse_yaml(file_content)
    else:
        return check_bracket_balance(file_content)


def parse_python(code):
    try:
        ast.parse(code)
        return "Valid syntax"
    except SyntaxError as e:
        return f"Syntax Error: {e.msg} (line {e.lineno - 1})"
    except Exception as e:
        return f"Error: {e}"


def parse_html(html_content):
    parser = etree.HTMLParser(recover=True)  # Enable recovery mode
    try:
        html_tree = etree.fromstring(html_content, parser)
        significant_errors = [
            error for error in parser.error_log
            # Shut down some error types to be able to parse html from vue
            #if not error.message.startswith('Tag')
            #and "error parsing attribute name" not in error.message
        ]
        if not significant_errors:
            return "Valid syntax"
        else:
            for error in significant_errors:
                return f"HTML line {error.line}: {error.message}"
    except etree.XMLSyntaxError as e:
        return f"Html error occurred: {e}"


def parse_template(code):
    for tag in ['div', 'p', 'span', 'main']:
        function_response = check_template_tag_balance(code, f'<{tag}', f'</{tag}>')
        if function_response != "Valid syntax":
            return function_response
    return "Valid syntax"


def parse_javascript(js_content):
    script_part_response = check_bracket_balance(js_content)
    if script_part_response != "Valid syntax":
        return script_part_response
    return "Valid syntax"


def check_template_tag_balance(code, open_tag, close_tag):
    opened_tags_count = 0
    open_tag_len = len(open_tag)
    close_tag_len = len(close_tag)

    i = 0
    while i < len(code):
        # check for open tag plus '>' or space after
        if code[i:i + open_tag_len] == open_tag and code[i + open_tag_len] in [' ', '>', '\n']:
            opened_tags_count += 1
            i += open_tag_len
        elif code[i:i + close_tag_len] == close_tag:
            opened_tags_count -= 1
            i += close_tag_len
            if opened_tags_count < 0:
                return f"Invalid syntax, mismatch of {open_tag} and {close_tag}"
        else:
            i += 1

    if opened_tags_count == 0:
        return "Valid syntax"
    else:
        return f"Invalid syntax, mismatch of {open_tag} and {close_tag}"


def bracket_balance(code, beginnig_bracket='{', end_bracket='}'):
    opened_brackets_count = 0

    for char in code:
        if char == beginnig_bracket:
            opened_brackets_count += 1
        elif char == end_bracket:
            opened_brackets_count -= 1
            if opened_brackets_count < 0:
                return f"Invalid syntax, mismatch of {beginnig_bracket} and {end_bracket}"

    if opened_brackets_count == 0:
        return "Valid syntax"
    else:
        return f"Invalid syntax, mismatch of {beginnig_bracket} and {end_bracket}"


def check_bracket_balance(code):
    bracket_response = bracket_balance(code, beginnig_bracket='(', end_bracket=')')
    if bracket_response != "Valid syntax":
        return bracket_response
    bracket_response = bracket_balance(code, beginnig_bracket='[', end_bracket=']')
    if bracket_response != "Valid syntax":
        return bracket_response
    bracket_response = bracket_balance(code, beginnig_bracket='{', end_bracket='}')
    if bracket_response != "Valid syntax":
        return bracket_response
    return "Valid syntax"


def parse_scss(scss_code):
    # removing import statements as they cousing error, because function has no access to filesystem
    scss_code = re.sub(r'@import\s+[\'"].*?[\'"];', '', scss_code)
    try:
        sass.compile(string=scss_code)
        return "Valid syntax"
    except sass.CompileError as e:
        return f"CSS/SCSS syntax error: {e}"


# That function does not guarantee finding all the syntax errors in template and script part; but mostly works
def parse_vue_basic(content):
    start_tag_template = re.search(r'<template>', content).end()
    end_tag_template = content.rindex('</template>')
    template = content[start_tag_template:end_tag_template]
    template_part_response = parse_template(template)
    if template_part_response != "Valid syntax":
        return template_part_response

    try:
        script = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL).group(1)
    except AttributeError:
        return "Script part has no valid open/closing tags."
    script_part_response = check_bracket_balance(script)
    if script_part_response != "Valid syntax":
        return script_part_response

    style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    if style_match:
        css = style_match.group(1)
        if css:     # if for the case of empty css block
            style_part_response = parse_scss(style_match.group(1))
            if style_part_response != "Valid syntax":
                return style_part_response

    return "Valid syntax"


# function works, but not used by default as there could be problems with esprima installation
def parse_javascript_esprima(js_content):
    import esprima
    try:
        esprima.parseModule(js_content)
        return "Valid syntax"
    except esprima.Error as e:
        print(f"Esprima syntax error: {e}")
        return f"JavaScript syntax error: {e}"


# Function under development
def lint_vue_code(code_string):
    import subprocess
    import os
    eslint_config_path = '.eslintrc.js'
    temp_file_path = "dzik.vue"
    # Create a temporary file
    with open(temp_file_path, 'w', encoding='utf-8') as file:
        file.write(code_string)
    try:
        # Run ESLint on the temporary file
        result = subprocess.run(['D:\\NodeJS\\npx.cmd', 'eslint', '--config', eslint_config_path, temp_file_path, '--fix'], check=True, text=True, capture_output=True)
        print("Linting successful:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error during linting:", e.stderr)
    finally:
        # Clean up by deleting the temporary file
        os.remove(temp_file_path)


def parse_tsx(tsx_code):
    template_response = parse_template(tsx_code)
    if template_response != "Valid syntax":
        return template_response
    bracket_balance_response = check_bracket_balance(tsx_code)
    if bracket_balance_response != "Valid syntax":
        return bracket_balance_response
    return "Valid syntax"


def parse_yaml(yaml_string):
    try:
        yaml.safe_load(yaml_string)
        return "Valid syntax"
    except yaml.YAMLError as e:
        return f"YAML error: {e}"



if __name__ == "__main__":
    code = """
"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, TextInput } from '../styles/uiElements';
import PopupNotification from '../components/PopupNotification';

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [notification, setNotification] = useState<{ message: string; type: 'positive' | 'negative' } | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotification(null);

    if (newPassword !== confirmNewPassword) {
      setNotification({ message: 'New passwords do not match.', type: 'negative' });
      return;
    }

    if (newPassword.length < 8) {
      setNotification({ message: 'Password must be at least 8 characters long.', type: 'negative' });
      return;
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          currentPassword,
          newPassword,
        }),
        credentials: 'include',
      });

      if (response.ok) {
        setNotification({ message: 'Password changed successfully!', type: 'positive' });
        setTimeout(() => {
          router.push('/profile');
        }, 2000);
      } else {
        let errorData;
        try {
          errorData = await response.json();
        } catch (parseError) {
          // fallback if no JSON is returned
          errorData = { detail: 'Unknown error occurred' };
        }
        if (response.status === 400) {
          setNotification({ message: errorData.detail || 'Bad request.', type: 'negative' });
        } else if (response.status === 401) {
          setNotification({ message: errorData.detail || 'Unauthorized. Please log in again.', type: 'negative' });
        } else {
          setNotification({ message: errorData.detail || 'Error changing password.', type: 'negative' });
        }
      }
    } catch (networkError) {
      setNotification({ message: 'Network error. Please try again.', type: 'negative' });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm p-8">
        <h1 className="text-2xl font-semibold text-center mb-8">Change Password</h1>

        {notification && (
          <PopupNotification
            message={notification.message}
            type={notification.type}
            onClose={() => setNotification(null)}
          />
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <TextInput
            label="Current Password"
            type="password"
            value={currentPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
            required
          />
          <TextInput
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
            required
          />
          <TextInput
            label="Confirm New Password"
            type="password"
            value={confirmNewPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmNewPassword(e.target.value)}
            required
          />
          <Button type="submit">Change Password</Button>
        </form>

        <div className="text-center mt-6">
          <a
            href="/profile"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Back to Profile
          </a>
        </div>
      </div>
    </div>
  );
}
"""
    print(parse_tsx(code))