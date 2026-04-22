import { useState } from "react";
import api from "../services/api";

function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    try {
      if (isRegister) {
        await api.post("/auth/register", {
          full_name: fullName,
          username,
          email,
          password,
        });

        setSuccess("Đăng ký thành công. Vui lòng đăng nhập.");
        setIsRegister(false);
        setPassword("");
        setIdentifier(email);
        return;
      }

      const loginPayload = identifier.includes("@")
        ? { email: identifier, password }
        : { username: identifier, password };

      const loginResponse = await api.post("/auth/login", loginPayload);
      onLogin({
        accessToken: loginResponse.data.access_token,
        refreshToken: loginResponse.data.refresh_token,
      });
    } catch (requestError) {
      const fallbackMessage = isRegister ? "Đăng ký thất bại" : "Đăng nhập thất bại";
      setError(requestError.response?.data?.detail || fallbackMessage);
    }
  };

  const handleToggleMode = () => {
    setIsRegister(!isRegister);
    setError("");
    setSuccess("");
    setPassword("");
  };

  return (
    <div className="container auth-container">
      <div className="card auth-card">
        <h1 className="auth-title">Quản Lý Tài Chính</h1>
        <p className="auth-subtitle">
          {isRegister ? "Tạo tài khoản mới để bắt đầu" : "Đăng nhập để tiếp tục quản lý tài chính"}
        </p>

        <form onSubmit={handleSubmit} className="form">
          {isRegister && (
            <>
              <label className="field-label">Họ và tên</label>
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Nhập họ và tên"
                required
              />

              <label className="field-label">Tên đăng nhập</label>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="Nhập username"
                required
              />
            </>
          )}

          {isRegister ? (
            <>
              <label className="field-label">Email</label>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="Nhập email"
                required
              />
            </>
          ) : (
            <>
              <label className="field-label">Email hoặc username</label>
              <input
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                placeholder="Nhập email hoặc username"
                required
              />
            </>
          )}

          <label className="field-label">Mật khẩu</label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Nhập mật khẩu"
            required
          />

          {success && <small className="success">{success}</small>}
          {error && <small className="error">{error}</small>}
          <button className="btn btn-primary" type="submit">
            {isRegister ? "Đăng ký" : "Đăng nhập"}
          </button>
        </form>

        <button className="link switch-mode" onClick={handleToggleMode}>
          {isRegister ? "Đã có tài khoản? Đăng nhập" : "Chưa có tài khoản? Đăng ký ngay"}
        </button>
      </div>
    </div>
  );
}

export default LoginPage;
