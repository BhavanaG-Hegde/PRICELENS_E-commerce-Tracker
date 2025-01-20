document.addEventListener('DOMContentLoaded', function () {
    const deleteForms = document.querySelectorAll('.delete-form');

    deleteForms.forEach(form => {
        form.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent default form submission

            const productImageUrl = this.querySelector('input[name="tracked_product_image_url"]').value;
            console.log('Tracked Product Image URL:', productImageUrl); // Debug statement

            if (!confirm('Are you sure you want to delete this product?')) {
                console.log('Deletion cancelled by user.'); // Debug statement
                return;
            }

            console.log('Sending DELETE request for Product with Image URL:', productImageUrl); // Debug statement
            fetch('/delete_product', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ tracked_product_image_url: productImageUrl }) // Send image_url in the body
            })
            .then(response => {
                console.log('Response status:', response.status); // Debug statement
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data); // Debug statement
                if (data.success) {
                    alert(data.message || 'Product deleted successfully');
                    // Reload the page to reflect changes
                    window.location.reload();
                } else {
                    alert(data.error || 'Error deleting product');
                }
            })
            .catch(error => {
                console.error('Error occurred during the request:', error); // Debug statement
            });
        });
    });
});
