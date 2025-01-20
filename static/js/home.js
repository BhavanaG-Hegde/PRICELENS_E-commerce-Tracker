// Trigger the product search
function triggerProductSearch() {
    const query = document.getElementById('searchBar').value.trim();
    if (query) {
        fetchAmazonProducts(query);
    } else {
        alert('Please enter a search query.');
    }
}

// Debounce to prevent excessive API calls while typing
let debounceTimeout;
function debounceSearch() {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
        const query = document.getElementById('searchBar').value.trim();
        if (query) {
            fetchAmazonProducts(query);
        }
    }, 500); // Adjust debounce delay as needed
}

async function fetchAmazonProducts(query) {
    try {
        const response = await fetch(`/api/scraped-products?query=${encodeURIComponent(query)}`);
        const products = await response.json();

        if (response.status !== 200 || products.error) {
            console.error('Error fetching products:', products.error);
            return;
        }

        // Populate the products on the page
        renderProducts(products);
    } catch (error) {
        console.error('Error fetching Amazon products:', error);
    }
}


function renderProducts(products) {
    const container = document.getElementById('scraped-products-container');
    container.innerHTML = ''; // Clear previous results

    products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'col-md-3';

        productCard.innerHTML = `
            <div class="card h-100 d-flex flex-column">
                <img src="${product.image_url || 'https://via.placeholder.com/150'}" class="card-img-top" alt="${product.name}" style="height: 200px; object-fit: contain; padding-top:5px;">
                <div class="card-body d-flex flex-column justify-content-between">
                    <h5 class="card-title" style="font-size: 1rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${product.name}</h5>
                    <p class="card-text" style="font-size: 1.1rem; font-weight: bold;">₹${product.price}</p>
                    <div class="d-flex justify-content-between mt-auto">
                        <a href="${product.link}" target="_blank" class="btn btn-primary btn-sm w-48">View Product</a>
                        <button class="btn btn-success btn-sm w-48" 
                            onclick="addToTrack('${product.name}', '${product.price}', '${product.link}', '${product.image_url}')">
                            Add to Track
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(productCard);
    });
}




/*top-deals only*/
async function fetchTopDeals() {
    try {
        const response = await fetch('/api/top-deals');
        const deals = await response.json();
        const dealsContainer = document.getElementById('top-deals');

        // Function to truncate product names to 7 words
        function truncateProductName(name) {
            const maxWords = 5; // Limit to 7 words
            const words = name.split(" ");
            return words.length > maxWords ? words.slice(0, maxWords).join(" ") + "..." : name;
        }

        deals.forEach(deal => {
            const dealCard = document.createElement('div');
            dealCard.className = 'col-md-3';

            // Truncate the deal name to 7 words
            const truncatedName = truncateProductName(deal.name);

            dealCard.innerHTML = `
                <div class="card deal-card">
                    <img src="${deal.image_url || 'https://via.placeholder.com/150'}" class="card-img-top deal-image" alt="${deal.name}">
                    <div class="card-body text-center">
                        <h5 class="deal-title">${truncatedName}</h5>
                        <p class="deal-price">₹${deal.price}</p>
                        <a href="${deal.link}" target="_blank" class="btn btn-deal">View Deal</a>
                    </div>
                </div>
            `;
            dealsContainer.appendChild(dealCard);

            // Ensure deal name occupies at least 3 lines
            const dealTitle = dealCard.querySelector('.deal-title');
            
            // Wait for the content to load
            setTimeout(() => {
                const lineHeight = parseInt(window.getComputedStyle(dealTitle).lineHeight);
                const height = dealTitle.offsetHeight;
                const requiredHeight = lineHeight * 3; // 3 lines of text

                // If the text height is less than 3 lines, add empty lines
                if (height < requiredHeight) {
                    const emptyLines = Math.floor((requiredHeight - height) / lineHeight);
                    for (let i = 0; i < emptyLines; i++) {
                        dealTitle.innerHTML += '<br>';
                    }
                }
            }, 0);
        });
    } catch (error) {
        console.error('Error fetching top deals:', error);
    }
}

document.addEventListener('DOMContentLoaded', fetchTopDeals);


async function logout() {
    try {
        const response = await fetch("/logout", {
            method: "GET",
        });
        if (response.redirected) {
                // Redirect to the page set in the Flask route
            window.location.href = response.url;
        }
     } catch (error) {
        console.error("Logout failed:", error);
     }
}

async function addToTrack(name, price, link, image_url) {
    try {
        const productData = { name, price, link, image_url };
        console.log(productData)
        const response = await fetch('/api/add-to-track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData),
        });

        const result = await response.json();
        if (result.success) {
            alert("Product added to tracking list!");
        } else {
            alert(`Failed to add product: ${result.error}`);
        }
    } catch (error) {
        console.error("Error adding product to track:", error);
    }
}
