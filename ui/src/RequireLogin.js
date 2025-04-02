import Login from "./Login.js";

function RequireLogin({ page, loggedIn, setLoggedIn, setSessionUsername }) {
  return loggedIn ? (
    page
  ) : (
    <Login
      loggedIn={loggedIn}
      setLoggedIn={setLoggedIn}
      setSessionUsername={setSessionUsername}
    />
  );
}

export default RequireLogin;
