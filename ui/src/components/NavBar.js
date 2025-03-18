import React, {useState} from 'react';
import { Link } from 'react-router-dom';
import "./NavBar.css";

function NavBar() {
  return (
    <>
      <nav className='navbar'>
        <div className='logo'>OpenPantry</div>
        <ul className='nav-links'>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/listings">Listings</Link></li>
            <li><Link to="/profile">Profile</Link></li>
        </ul>
      </nav>
    </>
  )
}

export default NavBar
