export function setCompareProduct(barcode) {
    localStorage.setItem("compare_1", barcode);
  }
  
  export function getCompareProduct() {
    return localStorage.getItem("compare_1");
  }
  
  export function clearCompare() {
    localStorage.removeItem("compare_1");
  }