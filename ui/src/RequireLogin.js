import Login from "./Login.js";

function RequireLogin({page, loggedIn, setLoggedIn}) {
    return loggedIn ? (
        page
    ) : (
        <Login loggedIn={loggedIn} setLoggedIn={setLoggedIn} />
    );
}

export default RequireLogin;
