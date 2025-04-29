import React from 'react';
import { Link } from 'react-router-dom';
import "./NavBar.css";

function NavBar({links}) {
  return (
    <>
      <nav className='navbar'>
        <div className="nav-links">
          <Link to="/">OpenPantry</Link>
          <div className="spacer" />
          {links.map(link => <Link
          key={link.title}
          to={link.path}>
            {link.title}
          </Link>)}
        </div>
      </nav>
    </>
  )
}

export default NavBar
