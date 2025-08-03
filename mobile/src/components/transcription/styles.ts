import { StyleSheet, Platform } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  
  // Audio Player Styles
  audioPlayer: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  playButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#F0F0F0',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: 16,
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  slider: {
    flex: 1,
    height: 40,
    marginHorizontal: 8,
  },
  timeText: {
    fontSize: 12,
    color: '#666666',
    minWidth: 45,
    textAlign: 'center',
  },
  
  // Search Bar Styles
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    margin: 16,
    marginBottom: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#333333',
    padding: 0,
  },
  
  // Action Bar Styles
  actionBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  actionButtonText: {
    marginLeft: 6,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  
  // Transcript Container Styles
  transcriptContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  
  // Segment Styles
  segment: {
    backgroundColor: '#FFFFFF',
    marginVertical: 8,
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  currentSegment: {
    borderColor: '#007AFF',
    borderWidth: 2,
    backgroundColor: '#F0F8FF',
  },
  segmentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  speakerBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  speakerName: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  timestamp: {
    fontSize: 12,
    color: '#666666',
  },
  segmentText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333333',
  },
  editInput: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333333',
    borderWidth: 1,
    borderColor: '#007AFF',
    borderRadius: 4,
    padding: 8,
    backgroundColor: '#FAFAFA',
  },
  
  // Entity Styles
  entity: {
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 4,
    marginHorizontal: 2,
  },
  entityDefault: {
    backgroundColor: '#E8F4FD',
  },
  entityPERSON: {
    backgroundColor: '#FFE4E1',
  },
  entityORG: {
    backgroundColor: '#E1F5FE',
  },
  entityLOC: {
    backgroundColor: '#E8F5E9',
  },
  entityDATE: {
    backgroundColor: '#FFF3E0',
  },
  entityMONEY: {
    backgroundColor: '#F3E5F5',
  },
  entitySelected: {
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  entityText: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    paddingBottom: Platform.OS === 'ios' ? 40 : 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333333',
    marginBottom: 24,
    textAlign: 'center',
  },
  exportOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  exportOptionText: {
    flex: 1,
    marginLeft: 16,
    fontSize: 16,
    color: '#333333',
  },
  cancelButton: {
    marginTop: 8,
    borderBottomWidth: 0,
    justifyContent: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
  },
});

export default styles;