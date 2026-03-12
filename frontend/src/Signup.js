import { useState } from "react";
import { apiFetch } from "./api";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const nav = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    k_number: "",
    department: "",
  });
  const [err, setErr] = useState("");

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
      await apiFetch("/auth/register/", {
        method: "POST",
        body: JSON.stringify(form),
      });
      nav("/login");
    } catch (e2) {
      setErr(String(e2.message));
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto" }}>
      <h2>Sign up</h2>
      {err && <p style={{ color: "crimson" }}>{err}</p>}
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
        {["username","email","password","first_name","last_name","k_number","department"].map((k) => (
          <input
            key={k}
            name={k}
            type={k === "password" ? "password" : "text"}
            placeholder={k.replaceAll("_", " ")}
            value={form[k]}
            onChange={onChange}
            required={["username","email","password","k_number"].includes(k)}
          />
        ))}
        <button type="submit">Create account</button>
      </form>
    </div>
  );
}
