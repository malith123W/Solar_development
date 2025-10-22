// Feeder names extracted from LECO directory structure
export const LECO_FEEDER_NAMES = [
  '0700082108', '0700188511', '0700759004', '0701114909', '0701369108',
  '0701379602', '0701433502', '0702285903', '0702365202', '0703235203',
  '0703635504', '0705065009', '0706739506', '0706778501', '0706867711',
  '0707058011', '0707425301', '0708123911', '0708929001'
];

// Function to get feeder names from uploaded NMD data
export const getFeederNamesFromNMD = (nmdData) => {
  if (!nmdData || !nmdData.feeders) {
    return LECO_FEEDER_NAMES; // Fallback to predefined names
  }
  
  // Return the feeders detected from the NMD file
  return nmdData.feeders;
};

// Function to validate feeder name
export const isValidFeederName = (feederName) => {
  return LECO_FEEDER_NAMES.includes(feederName);
};

// Function to get feeder display name
export const getFeederDisplayName = (feederName) => {
  return `Feeder ${feederName}`;
};
