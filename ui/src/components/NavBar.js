import React from 'react';
import { Link } from 'react-router-dom';
import "./NavBar.css";

function NavBar() {
  return (
    <>
      <nav className='navbar'>
        <div className="nav-links">
          <Link to="/">OpenPantry</Link>
          <div className="spacer" />
          <Link to="/pantry">Pantry</Link>
          <Link to="/listings">Listings</Link>
          <Link to="/profile">Profile</Link>
          <p>Log Out</p>
        </div>
      </nav>
    </>
  )
}

export default NavBar
