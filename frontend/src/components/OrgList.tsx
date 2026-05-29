import { useState, useEffect } from 'react';
import { fetchOrgs, Organization } from '../api';

export default function OrgList() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [ntee, setNtee] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchOrgs({ page: String(page), q: search, ntee, per_page: '20' })
      .then(data => {
        setOrgs(data.organizations);
        setTotal(data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, search, ntee]);

  const pages = Math.ceil(total / 20);

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h1>Daanaa Organizations</h1>
      <p>{total.toLocaleString()} nonprofits in database</p>
      
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <input 
          placeholder="Search name or EIN..." 
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
          style={{ padding: 8, flex: 1 }}
        />
        <select value={ntee} onChange={e => { setNtee(e.target.value); setPage(1); }}>
          <option value="">All Categories</option>
          <option value="A">Arts</option>
          <option value="B">Education</option>
          <option value="E">Health</option>
          <option value="P">Human Services</option>
          <option value="S">Community</option>
          <option value="X">Religion</option>
        </select>
      </div>

      {loading && <p>Loading...</p>}
      
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #333', textAlign: 'left' }}>
            <th>Name</th>
            <th>City</th>
            <th>State</th>
            <th>Category</th>
            <th>Revenue</th>
            <th>Percentile</th>
          </tr>
        </thead>
        <tbody>
          {orgs.map(org => (
            <tr key={org.EIN} style={{ borderBottom: '1px solid #ddd' }}>
              <td>
                <a href={`/org/${org.EIN}`} style={{ textDecoration: 'none', color: '#0066cc' }}>
                  {org.organization_name}
                </a>
              </td>
              <td>{org.CITY}</td>
              <td>{org.STATE}</td>
              <td>{org.NTEE1}</td>
              <td>{org.total_revenue_formatted}</td>
              <td>{org.ntee1_percentile}%</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 20, display: 'flex', gap: 10, alignItems: 'center' }}>
        <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
        <span>Page {page} of {pages}</span>
        <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}>Next →</button>
      </div>
    </div>
  );
}
