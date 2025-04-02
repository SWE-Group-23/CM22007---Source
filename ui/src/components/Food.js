function Food({foodItem, setPostingListing, setListingItem}) {
  return <div className="food-item">
    <h3>{foodItem.name}</h3>
    <p>Expires: {foodItem.exp}</p>
    <p>{foodItem.desc}</p>
    <img src="/bananas.jpg" />
    <div className="button-group jc-center-margin">
    <button className="dark-button" onClick={
      () => {
        setListingItem(foodItem);
        setPostingListing(true);
      }
    }>
      Post Listing
    </button>
    </div>
  </div>
}

export default Food;
