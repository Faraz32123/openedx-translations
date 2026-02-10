#!/usr/bin/env python3
import os
import polib

BASE_DIR = "/Users/faraz.maqsood/Desktop/tutor_setup/openedx-translations/translations/edx-platform/conf/locale/en/LC_MESSAGES"

def should_skip_entry(msgid: str) -> bool:
    """Check if we should skip this entry (leave msgstr empty)"""
    import re
    
    # Skip if msgid is empty or just whitespace
    if not msgid or msgid.strip() == "":
        return True
    
    # Skip if msgid contains only variable placeholders
    # Remove all {variable} patterns and see if anything substantial remains
    without_vars = re.sub(r'\{[^}]+\}', '', msgid)
    without_vars = re.sub(r'\s+', '', without_vars)  # Remove all whitespace
    
    # If nothing remains after removing variables, skip it
    if len(without_vars) == 0:
        return True
    
    # Also skip if it's very short and contains variables (likely just a variable)
    if len(msgid.strip()) < 20 and re.search(r'\{[^}]*course[^}]*\}', msgid):
        return True
    
    return False

def replace_course_words(text: str) -> str:
    """Replace course-related words with module equivalents, but preserve variable names exactly"""
    import re
    
    # Handle multi-line strings by replacing each line separately
    if isinstance(text, str) and '\n' in text:
        lines = text.split('\n')
        replaced_lines = []
        for line in lines:
            replaced_line = replace_course_words(line)
            replaced_lines.append(replaced_line)
        return '\n'.join(replaced_lines)
    else:
        # Find ALL variable placeholders and preserve them exactly
        # This is more comprehensive - we find all {anything} patterns
        var_placeholders = re.findall(r'\{[^}]+\}', text)
        
        # Also find common course-related variable patterns that might not have braces
        additional_patterns = [
            'course_url', 'courseware_title_linked', 'course_name', 'course_number', 'course_title', 
            'course_display_name', 'course_names', 'number_of_courses', 'courseName', 'course_about_url',
            'course.display_number_with_default', 'course_mode', 'start_date', 'end_date', 'course_id'
        ]
        
        # Add these to placeholders if they exist in text
        for pattern in additional_patterns:
            if pattern in text:
                var_placeholders.append(f'{{{pattern}}}')
        
        # Create temporary placeholders for all variables
        placeholders = {}
        for i, placeholder in enumerate(var_placeholders):
            temp_placeholder = f"__VAR_{i}__"
            text = text.replace(placeholder, temp_placeholder)
            placeholders[temp_placeholder] = placeholder
        
        # Now do the course->module replacement on the remaining text
        result = (
            text.replace("Courses", "Modules")
                .replace("courses", "modules")
                .replace("Course", "Module")
                .replace("course", "module")
        )
        
        # Restore the original variable names exactly
        for temp_placeholder, original_placeholder in placeholders.items():
            result = result.replace(temp_placeholder, original_placeholder)
        
        return result

def process_po_file(path):
    """Process a single PO file and add msgstr for course-related entries"""
    print(f"Processing {path}")
    po = polib.pofile(path)

    changed = False

    for entry in po:
        # Process singular entries
        if entry.msgid and "course" in entry.msgid.lower():
            # Skip entries that should be left empty
            if should_skip_entry(entry.msgid):
                if entry.msgstr:
                    entry.msgstr = ""
                    changed = True
                    print(f"  Cleared: '{entry.msgid}' (variables only)")
                continue
            
            # Only process if msgstr is empty or doesn't contain the replacement
            if not entry.msgstr or "course" in entry.msgstr.lower():
                new_text = replace_course_words(entry.msgid)
                if entry.msgstr != new_text:
                    entry.msgstr = new_text
                    changed = True
                    print(f"  Updated: '{entry.msgid}' -> '{entry.msgstr}'")

        # Process plural entries
        if entry.msgid_plural and "course" in entry.msgid_plural.lower():
            # Skip entries that should be left empty
            if should_skip_entry(entry.msgid_plural):
                if entry.msgstr_plural.get(0):
                    entry.msgstr_plural[0] = ""
                    changed = True
                    print(f"  Cleared plural: '{entry.msgid_plural}' (variables only)")
                continue
            
            # Process singular form
            if not entry.msgstr_plural.get(0) or "course" in entry.msgstr_plural[0].lower():
                singular = replace_course_words(entry.msgid)
                if entry.msgstr_plural.get(0) != singular:
                    entry.msgstr_plural[0] = singular
                    changed = True
                    print(f"  Updated singular: '{entry.msgid}' -> '{entry.msgstr_plural[0]}'")

            # Process plural form
            if not entry.msgstr_plural.get(1) or "course" in entry.msgstr_plural[1].lower():
                plural = replace_course_words(entry.msgid_plural)
                if entry.msgstr_plural.get(1) != plural:
                    entry.msgstr_plural[1] = plural
                    changed = True
                    print(f"  Updated plural: '{entry.msgid_plural}' -> '{entry.msgstr_plural[1]}'")

    if changed:
        po.save()
        print(f"✓ Updated {path}")
    else:
        print(f"- No changes needed for {path}")

def main():
    """Main function to process all PO files"""
    total_files = 0
    updated_files = 0
    
    for root, _, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith(".po"):
                total_files += 1
                try:
                    process_po_file(os.path.join(root, f))
                    updated_files += 1
                except Exception as e:
                    print(f"Error processing {os.path.join(root, f)}: {e}")
    
    print(f"\nSummary: Processed {updated_files}/{total_files} files successfully")

if __name__ == "__main__":
    main()
