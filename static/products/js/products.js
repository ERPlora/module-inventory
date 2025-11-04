/**
 * Products Plugin JavaScript
 * Manages product CRUD operations and data interactions
 */

class ProductsManager {
    constructor() {
        this.products = [];
        this.searchQuery = '';
        this.currentPage = 1;
        this.perPage = 10;
        this.totalPages = 1;
        this.total = 0;
        this.stats = {
            total: 0,
            in_stock: 0,
            low_stock: 0,
            value: 0
        };
    }

    /**
     * Initialize the products manager
     */
    async init() {
        await this.loadProducts();
    }

    /**
     * Load products from API
     */
    async loadProducts() {
        try {
            const url = `/products/api/list/?search=${encodeURIComponent(this.searchQuery)}&page=${this.currentPage}&per_page=${this.perPage}`;
            const response = await fetch(url);
            const data = await response.json();

            this.products = data.products;
            this.total = data.total;
            this.totalPages = data.pages;
            this.currentPage = data.current_page;

            return data;
        } catch (error) {
            console.error('Error loading products:', error);
            await this.showToast('Error al cargar productos', 'danger');
            throw error;
        }
    }

    /**
     * Search products
     */
    async searchProducts() {
        this.currentPage = 1;
        return await this.loadProducts();
    }

    /**
     * Navigate to previous page
     */
    async prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            return await this.loadProducts();
        }
    }

    /**
     * Navigate to next page
     */
    async nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            return await this.loadProducts();
        }
    }

    /**
     * Open modal to create/edit product
     */
    async openProductModal(product = null) {
        const isEdit = product !== null;
        const modal = document.createElement('ion-modal');

        // Modal configuration with responsive dimensions
        modal.style.cssText = `
            --width: 90%;
            --max-width: 600px;
            --min-height: 500px;
            --max-height: 90%;
            --border-radius: 16px;
        `;

        modal.innerHTML = `
            <ion-header>
                <ion-toolbar>
                    <ion-title>${isEdit ? 'Editar Producto' : 'Nuevo Producto'}</ion-title>
                    <ion-buttons slot="end">
                        <ion-button onclick="this.closest('ion-modal').dismiss()">
                            <ion-icon name="close"></ion-icon>
                        </ion-button>
                    </ion-buttons>
                </ion-toolbar>
            </ion-header>

            <ion-content class="ion-padding" style="--overflow: hidden;">
                <form id="productForm" class="flex flex-col h-full" style="min-height: 400px;">
                    <!-- Contenido con scroll interno -->
                    <div style="flex: 1; overflow-y: auto; padding-right: 8px;">
                        <ion-list lines="full">
                            <ion-item>
                                <ion-label position="stacked">Nombre *</ion-label>
                                <ion-input
                                    name="name"
                                    type="text"
                                    placeholder="Nombre del producto"
                                    value="${product?.name || ''}"
                                    required>
                                </ion-input>
                            </ion-item>

                            <ion-item>
                                <ion-label position="stacked">SKU *</ion-label>
                                <ion-input
                                    name="sku"
                                    type="text"
                                    placeholder="Código único"
                                    value="${product?.sku || ''}"
                                    required>
                                </ion-input>
                            </ion-item>

                            <ion-item>
                                <ion-label position="stacked">Categoría</ion-label>
                                <ion-input
                                    name="category"
                                    type="text"
                                    placeholder="Categoría"
                                    value="${product?.category || 'general'}">
                                </ion-input>
                            </ion-item>

                            <ion-item>
                                <ion-label position="stacked">Precio *</ion-label>
                                <ion-input
                                    name="price"
                                    type="number"
                                    placeholder="0.00"
                                    value="${product?.price || ''}"
                                    step="0.01"
                                    min="0"
                                    required>
                                </ion-input>
                            </ion-item>

                            <ion-item>
                                <ion-label position="stacked">Costo</ion-label>
                                <ion-input
                                    name="cost"
                                    type="number"
                                    placeholder="0.00"
                                    value="${product?.cost || 0}"
                                    step="0.01"
                                    min="0">
                                </ion-input>
                            </ion-item>

                            <ion-item>
                                <ion-label position="stacked">Stock</ion-label>
                                <ion-input
                                    name="stock"
                                    type="number"
                                    placeholder="0"
                                    value="${product?.stock || 0}"
                                    min="0">
                                </ion-input>
                            </ion-item>

                            <ion-item>
                                <ion-label position="stacked">Umbral de Stock Bajo</ion-label>
                                <ion-input
                                    name="low_stock_threshold"
                                    type="number"
                                    placeholder="10"
                                    value="${product?.low_stock_threshold || 10}"
                                    min="0">
                                </ion-input>
                            </ion-item>

                            ${isEdit ? `
                            <ion-item>
                                <ion-label position="stacked">Imagen del Producto</ion-label>
                                <input
                                    type="file"
                                    name="image"
                                    accept="image/*"
                                    style="margin-top: 8px;">
                            </ion-item>
                            ` : ''}
                        </ion-list>
                    </div>

                    <!-- Botones fijos en la parte inferior -->
                    <div class="flex gap-3 mt-4" style="flex-shrink: 0; padding-top: 16px; border-top: 1px solid var(--ion-border-color);">
                        <ion-button expand="block" fill="outline" onclick="this.closest('ion-modal').dismiss()">
                            Cancelar
                        </ion-button>
                        <ion-button expand="block" color="primary" type="submit">
                            ${isEdit ? 'Actualizar' : 'Crear'}
                        </ion-button>
                    </div>
                </form>
            </ion-content>
        `;

        document.body.appendChild(modal);
        await modal.present();

        // Handle form submission
        const form = modal.querySelector('#productForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const data = {};
            for (const [key, value] of formData.entries()) {
                if (key === 'image' && !value.name) continue; // Skip empty file input
                data[key] = value;
            }

            if (isEdit) {
                await this.updateProduct(product.id, data);
            } else {
                await this.createProduct(data);
            }

            await modal.dismiss();
        });
    }

    /**
     * Create a new product
     */
    async createProduct(data) {
        try {
            const formData = new FormData();
            for (const [key, value] of Object.entries(data)) {
                formData.append(key, value);
            }

            const response = await fetch('/products/create/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();
            if (result.success) {
                await this.showToast('Producto creado exitosamente', 'success');
                await this.loadProducts();
            } else {
                await this.showToast(result.message, 'danger');
            }
        } catch (error) {
            console.error('Error creating product:', error);
            await this.showToast('Error al crear producto', 'danger');
        }
    }

    /**
     * Update an existing product
     */
    async updateProduct(id, data) {
        try {
            const formData = new FormData();
            for (const [key, value] of Object.entries(data)) {
                formData.append(key, value);
            }

            const response = await fetch(`/products/edit/${id}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();
            if (result.success) {
                await this.showToast('Producto actualizado exitosamente', 'success');
                await this.loadProducts();
            } else {
                await this.showToast(result.message, 'danger');
            }
        } catch (error) {
            console.error('Error updating product:', error);
            await this.showToast('Error al actualizar producto', 'danger');
        }
    }

    /**
     * Delete a product with confirmation
     */
    async deleteProduct(product) {
        const alert = document.createElement('ion-alert');
        alert.header = 'Confirmar Eliminación';
        alert.message = `¿Estás seguro de que deseas eliminar el producto "${product.name}"?`;
        alert.buttons = [
            {
                text: 'Cancelar',
                role: 'cancel'
            },
            {
                text: 'Eliminar',
                role: 'destructive',
                handler: async () => {
                    try {
                        const response = await fetch(`/products/delete/${product.id}/`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': this.getCSRFToken()
                            }
                        });

                        const result = await response.json();
                        if (result.success) {
                            await this.showToast('Producto eliminado exitosamente', 'success');
                            await this.loadProducts();
                        } else {
                            await this.showToast(result.message, 'danger');
                        }
                    } catch (error) {
                        console.error('Error deleting product:', error);
                        await this.showToast('Error al eliminar producto', 'danger');
                    }
                }
            }
        ];

        document.body.appendChild(alert);
        await alert.present();
    }

    /**
     * Export products to CSV
     */
    exportCSV() {
        window.location.href = '/products/export/csv/';
    }

    /**
     * Open file picker for import
     */
    async openImportModal(type) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = type === 'csv' ? '.csv' : '.xlsx,.xls';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const url = type === 'csv' ? '/products/import/csv/' : '/products/import/excel/';
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });

                const result = await response.json();
                if (result.success) {
                    await this.showToast(`${result.message}`, 'success');
                    await this.loadProducts();
                } else {
                    await this.showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('Error importing file:', error);
                await this.showToast('Error al importar archivo', 'danger');
            }
        };
        input.click();
    }

    /**
     * Get CSRF token from page
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    /**
     * Show toast notification
     */
    async showToast(message, color = 'primary') {
        const toast = document.createElement('ion-toast');
        toast.message = message;
        toast.duration = 3000;
        toast.color = color;
        toast.position = 'top';
        document.body.appendChild(toast);
        await toast.present();
    }
}

// Export for use in templates
window.ProductsManager = ProductsManager;
