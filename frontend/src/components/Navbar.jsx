import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav style={{ padding: '10px', background: '#f2f2f2' }}>
      <Link to="/" style={{ marginRight: '10px' }}>Home</Link>
      <Link to="/jobanalyze" style={{ marginRight: '10px' }}>Skill Gap Analysis</Link>
    </nav>
  );
};

export default Navbar;
