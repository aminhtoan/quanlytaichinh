import { useEffect, useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));

  useEffect(() => {
    const onForceLogout = () => {
      localStorage.removeItem("refresh_token");
      setToken(null);
    };

    window.addEventListener("auth:logout", onForceLogout);
    return () => {
      window.removeEventListener("auth:logout", onForceLogout);
    };
  }, []);

  if (!token) {
    return (
      <LoginPage
        onLogin={({ accessToken, refreshToken }) => {
          localStorage.setItem("token", accessToken);
          if (refreshToken) {
            localStorage.setItem("refresh_token", refreshToken);
          }
          setToken(accessToken);
        }}
      />
    );
  }

  return (
    <DashboardPage
      onLogout={() => {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        setToken(null);
      }}
    />
  );
}

export default App;
