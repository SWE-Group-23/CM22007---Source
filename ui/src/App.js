import "./App.css";
import NavBar from "./components/NavBar";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

function Home() {
  <h2>Home Page</h2>
}

function Listings() {
  <h2>Listings Page</h2>
}

function Profile() {
  <h2>Profile Page</h2>
}

function Button1() {
  function handleClick() {
    alert("I've been clicked ahhhh!")
  }

  return(
    <button onClick = {handleClick}>
      Click me!
    </button>
  );
}

function App() {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/listings" element={<Listings />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Router>
  );
}

export default App;