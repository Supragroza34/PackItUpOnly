import React, { useMemo } from "react";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./RichTextEditor.css";

const ALLOWED_FORMATS = ["bold", "italic", "list", "indent"];

export default function RichTextEditor({
  id,
  value,
  onChange,
  placeholder,
  disabled = false,
  hasError = false,
}) {
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

  return (
    <div className={`rte-wrapper${hasError ? " rte-wrapper-error" : ""}`}>
      <ReactQuill
        id={id}
        theme="snow"
        value={value}
        onChange={onChange}
        modules={modules}
        formats={ALLOWED_FORMATS}
        placeholder={placeholder}
        readOnly={disabled}
      />
    </div>
  );
}
