import Login from "./Login.js";
import { Navigate } from "react-router-dom";

function RequireLogin({ page, loggedIn }) {
  return loggedIn ? page : <Navigate to="/login" />;
}
export default RequireLogin;
