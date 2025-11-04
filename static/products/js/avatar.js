/**
 * Avatar Component
 * Crea avatares con imagen o letra inicial para productos y categorías
 */

/**
 * Crea un elemento avatar con imagen o letra inicial
 * @param {Object} options - Opciones del avatar
 * @param {string} options.image - URL de la imagen (opcional)
 * @param {string} options.initial - Letra inicial (requerido si no hay imagen)
 * @param {string} options.name - Nombre completo para alt text
 * @param {string} options.color - Color de fondo en formato hex (opcional, default: #3880ff)
 * @param {string} options.size - Tamaño del avatar: 'small', 'medium', 'large' (default: 'medium')
 * @returns {string} HTML del avatar
 */
function createAvatar(options) {
    const {
        image = null,
        initial = '?',
        name = '',
        color = '#3880ff',
        size = 'medium'
    } = options;

    // Tamaños en píxeles
    const sizes = {
        'small': { width: 32, fontSize: 14 },
        'medium': { width: 40, fontSize: 16 },
        'large': { width: 56, fontSize: 20 }
    };

    const sizeConfig = sizes[size] || sizes.medium;
    const width = sizeConfig.width;
    const fontSize = sizeConfig.fontSize;

    // Si hay imagen, mostrar imagen
    if (image) {
        return `
            <div class="avatar" style="
                width: ${width}px;
                height: ${width}px;
                border-radius: 50%;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                background: var(--ion-color-light);
            ">
                <img
                    src="${image}"
                    alt="${name}"
                    style="
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                    "
                    onerror="this.parentElement.innerHTML = createAvatarFallback('${initial}', '${color}', ${fontSize})"
                >
            </div>
        `;
    }

    // Si no hay imagen, mostrar inicial
    return `
        <div class="avatar" style="
            width: ${width}px;
            height: ${width}px;
            border-radius: 50%;
            background: ${color};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: ${fontSize}px;
            text-transform: uppercase;
        ">
            ${initial}
        </div>
    `;
}

/**
 * Crea el fallback HTML cuando la imagen falla
 * @param {string} initial - Letra inicial
 * @param {string} color - Color de fondo
 * @param {number} fontSize - Tamaño de fuente
 * @returns {string} HTML del fallback
 */
function createAvatarFallback(initial, color, fontSize) {
    return `
        <div style="
            width: 100%;
            height: 100%;
            background: ${color};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: ${fontSize}px;
            text-transform: uppercase;
        ">
            ${initial}
        </div>
    `;
}

/**
 * Genera un color basado en el texto (para consistencia)
 * @param {string} text - Texto para generar el color
 * @returns {string} Color en formato hex
 */
function generateColorFromText(text) {
    if (!text) return '#3880ff';

    // Paleta de colores consistente
    const colors = [
        '#3880ff', // primary
        '#0cd1e8', // secondary
        '#10dc60', // success
        '#ffce00', // warning
        '#f04141', // danger
        '#7044ff', // tertiary
        '#5260ff', // indigo
        '#6a64ff', // purple
        '#f46eff', // pink
    ];

    // Calcular hash simple del texto
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        hash = text.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Seleccionar color basado en el hash
    const index = Math.abs(hash) % colors.length;
    return colors[index];
}

/**
 * Obtiene la primera letra de un texto
 * @param {string} text - Texto del cual extraer la inicial
 * @returns {string} Primera letra en mayúscula
 */
function getInitial(text) {
    if (!text || typeof text !== 'string') return '?';
    return text.charAt(0).toUpperCase();
}

// Exportar funciones para uso global
if (typeof window !== 'undefined') {
    window.createAvatar = createAvatar;
    window.createAvatarFallback = createAvatarFallback;
    window.generateColorFromText = generateColorFromText;
    window.getInitial = getInitial;
}
