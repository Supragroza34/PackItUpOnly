import React, { useMemo, useRef, useEffect } from "react";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./RichTextEditor.css";

const ALLOWED_FORMATS = ["bold", "italic", "list", "indent"];

// Function to sanitize HTML by removing disallowed formats
function sanitizeHtml(html) {
  if (!html) return "";
  
  // Create a temp container to parse HTML
  const temp = document.createElement("div");
  temp.innerHTML = html;
  
  // Remove all attributes except for those we explicitly allow
  const walk = (node) => {
    if (node.nodeType === Node.ELEMENT_NODE) {
      // For list items and divs with indent, preserve their structure
      // For other elements, remove all attributes
      if (node.tagName === "LI" || node.tagName === "OL" || node.tagName === "UL") {
        // Keep list structure intact
      } else if (node.tagName === "DIV" || node.tagName === "P") {
        // Check for data-indent attribute
        const indent = node.getAttribute("data-indent");
        // Remove all attributes properly
        while (node.attributes.length > 0) {
          node.removeAttribute(node.attributes[0].name);
        }
        if (indent) {
          node.setAttribute("data-indent", indent);
        }
      } else if (node.tagName === "BR") {
        // Keep BR tags
      } else if (!["STRONG", "EM", "B", "I", "OL", "UL", "LI"].includes(node.tagName)) {
        // For disallowed tags, replace with their content
        while (node.firstChild) {
          node.parentNode.insertBefore(node.firstChild, node);
        }
        node.parentNode.removeChild(node);
        return;
      }
    }
    
    if (node.childNodes) {
      Array.from(node.childNodes).forEach(walk);
    }
  };
  
  walk(temp);
  return temp.innerHTML;
}

export default function RichTextEditor({
  id,
  value,
  onChange,
  placeholder,
  disabled = false,
  hasError = false,
}) {
  const quillRef = useRef(null);

  const modules = useMemo(
    () => ({
      toolbar: [
        ["bold", "italic"],
        [{ list: "bullet" }, { list: "ordered" }],
        [{ indent: "-1" }, { indent: "+1" }],
      ],
      clipboard: {
        matchVisual: false,
      },
    }),
    []
  );

  useEffect(() => {
    if (quillRef.current && quillRef.current.editor) {
      const editor = quillRef.current.editor;
      
      // Prevent format operations not in ALLOWED_FORMATS
      const originalFormat = editor.getFormat.bind(editor);
      editor.getFormat = function(...args) {
        const format = originalFormat(...args);
        // Filter to only allowed formats
        const filtered = {};
        ALLOWED_FORMATS.forEach(fmt => {
          if (fmt in format) {
            filtered[fmt] = format[fmt];
          }
        });
        return filtered;
      };
    }
  }, []);

  // Sanitize value on change
  const handleChange = (content) => {
    const sanitized = sanitizeHtml(content);
    onChange(sanitized);
  };

  return (
    <div className={`rte-wrapper${hasError ? " rte-wrapper-error" : ""}`}>
      <ReactQuill
        ref={quillRef}
        id={id}
        theme="snow"
        value={value}
        onChange={handleChange}
        modules={modules}
        formats={ALLOWED_FORMATS}
        placeholder={placeholder}
        readOnly={disabled}
      />
    </div>
  );
}
