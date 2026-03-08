import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import staffApi from '../../services/staffApi';

export const reassignTicket = createAsyncThunk(
  'staff/reassignTicket',
  async ({ ticketId, updates }, { rejectWithValue }) => {
    try {
      const data = await staffApi.reassignTicket(ticketId, updates);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Staff List
export const fetchStaffList = createAsyncThunk(
  'staff/fetchStaffList',
  async (_, { rejectWithValue }) => {
    try {
      const data = await staffApi.getStaffList();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);


const staffSlice = createSlice({
  name: 'staff',
  initialState: {
    ticket: null,
    ticketLoading: false,
    error: null,

    // Staff List
    staffList: [],
    staffListLoading: false,
    staffListError: null,
  },
  reducers: {
    clearTicketsError: (state) => {
      state.ticketsError = null;
    },
    clearUsersError: (state) => {
      state.usersError = null;
    },
    setSelectedTicket: (state, action) => {
      state.selectedTicket = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Update Ticket
      .addCase(reassignTicket.pending, (state) => {
        state.loading = true;
      })      
      .addCase(reassignTicket.fulfilled, (state, action) => {
        state.loading = false;
        state.ticket = action.payload;
      })
      .addCase(reassignTicket.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error;
      })      
      
      // Staff List
      .addCase(fetchStaffList.pending, (state) => {
        state.staffListLoading = true;
      })
      .addCase(fetchStaffList.fulfilled, (state, action) => {
        state.staffListLoading = false;
        state.staffList = action.payload.staff || action.payload;
        state.staffListError = null;
      })
      .addCase(fetchStaffList.rejected, (state, action) => {
        state.staffListLoading = false;
        state.staffListError = action.payload;
      })
  },
});

export const { 
  clearTicketsError, 
  clearUsersError,
  setSelectedTicket,
} = staffSlice.actions;

export default staffSlice.reducer;
