function Food({foodItem, setPostingListing, setListingItem, removeItem}) {
  return <div className="food-item">
    <h3>{foodItem.name}</h3>
    <p>Expires: {foodItem.exp}</p>
    <p>{foodItem.desc}</p>
    <img src="/img/bananas.jpg" alt="bananas" />
    <div className="button-group jc-center-margin">
    <button className="light-button" onClick={
      () => {
        removeItem(foodItem.id);
      }
    }>
      Delete
    </button>
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
