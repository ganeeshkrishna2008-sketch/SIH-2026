// frontend/src/utils/vehicleType.js
// Centralized high-level vehicle category mapping for the SIH prototype

export const VEHICLE_TYPE_MAP = {
  car: 'Car',
  sedan: 'Car',
  suv: 'Car',
  motorcycle: 'Motorcycle',
  bike: 'Motorcycle',
  bus: 'Bus',
  truck: 'Truck',
  auto: 'Other',
  unknown: 'Other',
};

export const TARGET_VEHICLE_CATEGORIES = ['Car', 'Motorcycle', 'Bus', 'Truck', 'Other'];

export const CATEGORY_COLORS = {
  Car: '#38bdf8',        // Sky
  Truck: '#f59e0b',      // Amber
  Motorcycle: '#10b981', // Emerald
  Bus: '#a855f7',        // Purple
  Other: '#64748b',      // Slate
};

export function mapVehicleType(type) {
  if (!type) return 'Other';
  const clean = String(type).trim().toLowerCase();
  return VEHICLE_TYPE_MAP[clean] || 'Other';
}
