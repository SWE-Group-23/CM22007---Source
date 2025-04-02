function Profile({username}) {
  return <div className="profile-page">
        <img className="profile-image" src="blank.png" alt="A dark grey silhouette on a light grey background." />
        <p className="profile-name">{username}</p>
        <div className="profile-container">
            <label htmlFor="profile-bio" className="profile-label">Biography</label>
            <textarea type="text" className="profile-textarea" id="profile-bio" placeholder="Edit your biography..."/>
            <label htmlFor="profile-pref" className="profile-label">Dietary Requirements</label>
            <input type="text" className="profile-input" id="profile-pref" placeholder="Enter your dietary requirements..."/>
            <button className="profile-save-btn">Save changes</button>
        </div>
        </div>
}

export default Profile;
