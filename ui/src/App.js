import "./App.css";
import NavBar from "./components/NavBar";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

function Home() {
  return (<div className="title-page">
    <div className="title-box">OpenPantry</div>
    <div className="title-text">
Cook tasty healthy meals for less.
Reduce food waste at the same time.
    </div>
  </div>);
}

function Listings() {
    return <h2>Listings Page</h2>
}

function Profile() {
  return <div className="profile-page">
        <img className="profile-image" src="blank.png" alt="A dark grey silhouette on a light grey background." />
        <p className="profile-name">random-user654</p>
        </div>
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
