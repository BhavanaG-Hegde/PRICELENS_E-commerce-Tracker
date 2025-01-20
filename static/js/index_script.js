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
